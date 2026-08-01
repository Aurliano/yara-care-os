"""Synchronization session lifecycle."""

from __future__ import annotations

import uuid

from django.db import transaction
from django.utils import timezone

from domains.synchronization.enums import (
    RESUMABLE_SESSION_STATUSES,
    SessionStatus,
    SyncDirection,
)
from domains.synchronization.exceptions import (
    IdempotencyConflictError,
    InvalidSessionStateError,
    SessionNotFoundError,
)
from domains.synchronization.models import SynchronizationSession
from domains.synchronization.services.events import (
    emit_synchronization_cancelled,
    emit_synchronization_completed,
    emit_synchronization_failed,
    emit_synchronization_started,
)
from domains.synchronization.services.replicas import (
    get_or_create_replica_state,
    set_replica_idle,
    set_replica_synchronizing,
)


def get_synchronization_session(session_id: uuid.UUID) -> SynchronizationSession:
    try:
        return SynchronizationSession.objects.select_related("replica_state").get(pk=session_id)
    except SynchronizationSession.DoesNotExist as exc:
        raise SessionNotFoundError("Synchronization session not found.") from exc


def get_synchronization_history(*, replica_identifier: uuid.UUID, limit: int = 50) -> list[SynchronizationSession]:
    return list(
        SynchronizationSession.objects.filter(replica_state__replica_identifier=replica_identifier)
        .select_related("replica_state")
        .order_by("-started_at")[:limit]
    )


def _find_existing_session(idempotency_key: str | None) -> SynchronizationSession | None:
    if not idempotency_key:
        return None
    return SynchronizationSession.objects.filter(idempotency_key=idempotency_key).first()


def _transition_session(session: SynchronizationSession, status: str) -> SynchronizationSession:
    if session.status == status:
        return session
    session.status = status
    session.save(update_fields=["status", "updated_at"])
    return session


def _complete_session(session: SynchronizationSession) -> SynchronizationSession:
    if session.status == SessionStatus.SESSION_COMPLETED:
        return session
    session.status = SessionStatus.SESSION_COMPLETED
    session.completed_at = timezone.now()
    session.save(update_fields=["status", "completed_at", "updated_at"])
    set_replica_idle(session.replica_state)
    emit_synchronization_completed(session_id=session.id)
    return session


@transaction.atomic
def start_synchronization(
    *,
    replica_identifier: uuid.UUID,
    replica_type: str,
    direction: str,
    idempotency_key: str | None = None,
) -> SynchronizationSession:
    if direction not in SyncDirection.values:
        raise InvalidSessionStateError("Invalid synchronization direction.")

    existing = _find_existing_session(idempotency_key)
    if existing is not None:
        return existing

    replica = get_or_create_replica_state(
        replica_identifier=replica_identifier,
        replica_type=replica_type,
    )
    set_replica_synchronizing(replica)

    now = timezone.now()
    session = SynchronizationSession.objects.create(
        replica_state=replica,
        direction=direction,
        status=SessionStatus.SYNCHRONIZATION_REQUESTED,
        started_at=now,
        idempotency_key=idempotency_key,
    )
    _transition_session(session, SessionStatus.SESSION_STARTED)
    emit_synchronization_started(session_id=session.id, replica_identifier=replica_identifier)
    return session


@transaction.atomic
def resume_synchronization(*, session_id: uuid.UUID) -> SynchronizationSession:
    session = SynchronizationSession.objects.select_for_update().select_related("replica_state").get(pk=session_id)

    if session.status == SessionStatus.SESSION_COMPLETED:
        return session
    if session.status == SessionStatus.CANCELLED:
        raise InvalidSessionStateError("Cancelled sessions cannot be resumed.")
    if session.status not in RESUMABLE_SESSION_STATUSES and session.status != SessionStatus.SYNCHRONIZATION_RESUMED:
        if session.status not in {
            SessionStatus.SESSION_STARTED,
            SessionStatus.PAYLOAD_RECEIVED,
            SessionStatus.VALIDATION,
            SessionStatus.CHANGES_APPLIED,
            SessionStatus.CHECKPOINT_ADVANCED,
        }:
            raise InvalidSessionStateError("Session is not in a resumable state.")

    set_replica_synchronizing(session.replica_state)
    session.retry_count += 1
    session.status = SessionStatus.SYNCHRONIZATION_RESUMED
    session.save(update_fields=["retry_count", "status", "updated_at"])
    _transition_session(session, SessionStatus.SESSION_STARTED)
    return session


@transaction.atomic
def cancel_synchronization(*, session_id: uuid.UUID) -> SynchronizationSession:
    session = SynchronizationSession.objects.select_for_update().select_related("replica_state").get(pk=session_id)

    if session.status == SessionStatus.CANCELLED:
        return session
    if session.status == SessionStatus.SESSION_COMPLETED:
        raise InvalidSessionStateError("Completed sessions cannot be cancelled.")

    session.status = SessionStatus.CANCELLED
    session.cancelled_at = timezone.now()
    session.save(update_fields=["status", "cancelled_at", "updated_at"])
    set_replica_idle(session.replica_state)
    emit_synchronization_cancelled(session_id=session.id)
    return session


@transaction.atomic
def mark_transfer_failed(*, session_id: uuid.UUID, reason: str = "") -> SynchronizationSession:
    session = SynchronizationSession.objects.select_for_update().select_related("replica_state").get(pk=session_id)
    if session.status in {SessionStatus.SESSION_COMPLETED, SessionStatus.CANCELLED}:
        raise InvalidSessionStateError("Terminal sessions cannot fail.")

    session.status = SessionStatus.TRANSFER_FAILED
    session.save(update_fields=["status", "updated_at"])
    emit_synchronization_failed(session_id=session.id, reason=reason)

    session.status = SessionStatus.RETRY_SCHEDULED
    session.save(update_fields=["status", "updated_at"])
    set_replica_idle(session.replica_state)
    return session
