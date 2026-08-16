"""Communication session lifecycle and call attempts."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone

from common.observability.logging import log_structured
from common.observability.metrics import increment
from domains.communication.enums import (
    ACTIVE_SESSION_STATUSES,
    TERMINAL_SESSION_STATUSES,
    CallAttemptOutcome,
    CommunicationChannel,
    ParticipantRole,
    SessionOutcome,
    SessionStatus,
)
from domains.communication.exceptions import (
    ActiveSessionExistsError,
    CallAttemptNotFoundError,
    EntitlementDeniedError,
    InvalidSessionStateError,
    SessionNotFoundError,
)
from domains.communication.models import CallAttempt, CommunicationSession, Contact, SessionParticipant
from domains.communication.services.events import (
    emit_call_attempt_failed,
    emit_call_attempt_started,
    emit_session_connected,
    emit_session_declined,
    emit_session_ended,
    emit_session_failed,
    emit_session_initiated,
    emit_session_missed,
)
from domains.communication.versioning import bump_communication_session_version
from domains.licensing.enums import EntitlementKey
from domains.licensing.services.entitlements import can_use_feature

logger = logging.getLogger("yara.communication")


def get_active_session(*, elder_id: uuid.UUID) -> CommunicationSession | None:
    return (
        CommunicationSession.objects.filter(elder_id=elder_id, status__in=ACTIVE_SESSION_STATUSES)
        .order_by("-initiated_at")
        .first()
    )


def _ensure_no_active_session(*, elder_id: uuid.UUID) -> None:
    if get_active_session(elder_id=elder_id) is not None:
        raise ActiveSessionExistsError("An active communication session already exists for this elder.")


def get_session(session_id: uuid.UUID) -> CommunicationSession:
    try:
        return CommunicationSession.objects.prefetch_related("participants", "call_attempts").get(pk=session_id)
    except CommunicationSession.DoesNotExist as exc:
        raise SessionNotFoundError("Communication session not found.") from exc


def get_recent_sessions(*, elder_id: uuid.UUID, limit: int = 20) -> list[CommunicationSession]:
    return list(
        CommunicationSession.objects.filter(elder_id=elder_id).order_by("-initiated_at")[:limit]
    )


def get_session_participants(*, session_id: uuid.UUID) -> list[SessionParticipant]:
    return list(SessionParticipant.objects.filter(communication_session_id=session_id).order_by("role"))


def get_call_attempts(*, session_id: uuid.UUID) -> list[CallAttempt]:
    return list(CallAttempt.objects.filter(communication_session_id=session_id).order_by("attempt_number"))


def _ensure_not_terminal(session: CommunicationSession) -> None:
    if session.status in TERMINAL_SESSION_STATUSES:
        raise InvalidSessionStateError("Terminal sessions cannot be modified.")


def _validate_channel_entitlement(*, elder_id: uuid.UUID, channel: str) -> None:
    if channel == CommunicationChannel.VIDEO and not can_use_feature(elder_id, EntitlementKey.VIDEO_CALL.value):
        raise EntitlementDeniedError("VIDEO_CALL entitlement is required for video sessions.")


def _set_terminal(
    session: CommunicationSession,
    *,
    status: str,
    outcome: str,
    ended_at: datetime | None = None,
) -> CommunicationSession:
    now = ended_at or timezone.now()
    if session.connected_at and now < session.connected_at:
        raise InvalidSessionStateError("ended_at cannot be before connected_at.")

    session.status = status
    session.outcome = outcome
    session.ended_at = now
    update_fields = ["status", "outcome", "ended_at", "updated_at"]
    bump_communication_session_version(session, update_fields)
    session.save(update_fields=update_fields)
    return session


@transaction.atomic
def initiate_session(
    *,
    elder_id: uuid.UUID,
    channel: str,
    initiator_contact_id: uuid.UUID | None = None,
    initiator_user_id: uuid.UUID | None = None,
    recipient_contact_id: uuid.UUID,
    external_execution_reference: uuid.UUID | None = None,
) -> CommunicationSession:
    if channel not in CommunicationChannel.values:
        raise InvalidSessionStateError("Invalid communication channel.")

    _validate_channel_entitlement(elder_id=elder_id, channel=channel)
    _ensure_no_active_session(elder_id=elder_id)

    recipient = Contact.objects.get(pk=recipient_contact_id, elder_id=elder_id)
    if initiator_contact_id is not None:
        Contact.objects.get(pk=initiator_contact_id, elder_id=elder_id)

    now = timezone.now()
    session = CommunicationSession.objects.create(
        elder_id=elder_id,
        channel=channel,
        status=SessionStatus.INITIATED,
        initiated_at=now,
        external_execution_reference=external_execution_reference,
    )

    if initiator_contact_id is not None:
        SessionParticipant.objects.create(
            communication_session=session,
            contact_id=initiator_contact_id,
            role=ParticipantRole.INITIATOR,
        )
    else:
        SessionParticipant.objects.create(
            communication_session=session,
            user_id=initiator_user_id,
            role=ParticipantRole.INITIATOR,
        )

    SessionParticipant.objects.create(
        communication_session=session,
        contact=recipient,
        role=ParticipantRole.RECIPIENT,
    )

    emit_session_initiated(session_id=session.id, elder_id=elder_id, channel=channel)
    increment("communication.session.started")
    log_structured(
        logger,
        "communication.session.started",
        session_id=session.id,
        execution_id=external_execution_reference,
    )
    return session


@transaction.atomic
def accept_session(*, session_id: uuid.UUID) -> CommunicationSession:
    session = CommunicationSession.objects.select_for_update().get(pk=session_id)
    if session.status in TERMINAL_SESSION_STATUSES:
        if session.status == SessionStatus.CONNECTED:
            return session
        raise InvalidSessionStateError("Terminal sessions cannot be accepted.")

    now = timezone.now()
    if session.status in {SessionStatus.INITIATED, SessionStatus.CONNECTING}:
        session.status = SessionStatus.CONNECTED
        session.connected_at = now
        update_fields = ["status", "connected_at", "updated_at"]
        bump_communication_session_version(session, update_fields)
        session.save(update_fields=update_fields)
        emit_session_connected(session_id=session.id)
    return session


@transaction.atomic
def decline_session(*, session_id: uuid.UUID) -> CommunicationSession:
    session = CommunicationSession.objects.select_for_update().get(pk=session_id)
    if session.status in TERMINAL_SESSION_STATUSES:
        if session.status == SessionStatus.DECLINED:
            return session
        raise InvalidSessionStateError("Terminal sessions cannot be declined.")

    _set_terminal(session, status=SessionStatus.DECLINED, outcome=SessionOutcome.DECLINED)
    emit_session_declined(session_id=session.id)
    return session


@transaction.atomic
def cancel_session(*, session_id: uuid.UUID) -> CommunicationSession:
    session = CommunicationSession.objects.select_for_update().get(pk=session_id)
    if session.status in TERMINAL_SESSION_STATUSES:
        if session.status == SessionStatus.CANCELLED:
            return session
        raise InvalidSessionStateError("Terminal sessions cannot be cancelled.")

    _set_terminal(session, status=SessionStatus.CANCELLED, outcome=SessionOutcome.CANCELLED)
    emit_session_ended(
        session_id=session.id,
        outcome=SessionOutcome.CANCELLED,
        elder_id=session.elder_id,
        external_execution_reference=session.external_execution_reference,
    )
    return session


@transaction.atomic
def end_session(*, session_id: uuid.UUID) -> CommunicationSession:
    session = CommunicationSession.objects.select_for_update().get(pk=session_id)
    if session.status == SessionStatus.ENDED:
        return session
    if session.status in TERMINAL_SESSION_STATUSES:
        raise InvalidSessionStateError("Terminal sessions cannot be ended.")

    if session.status != SessionStatus.CONNECTED or session.connected_at is None:
        raise InvalidSessionStateError("Only connected sessions can be ended with ANSWERED outcome.")

    _set_terminal(session, status=SessionStatus.ENDED, outcome=SessionOutcome.ANSWERED)
    emit_session_ended(
        session_id=session.id,
        outcome=SessionOutcome.ANSWERED,
        elder_id=session.elder_id,
        external_execution_reference=session.external_execution_reference,
    )
    log_structured(
        logger,
        "communication.session.ended",
        session_id=session.id,
        execution_id=session.external_execution_reference,
    )
    return session


@transaction.atomic
def mark_session_missed(*, session_id: uuid.UUID) -> CommunicationSession:
    session = CommunicationSession.objects.select_for_update().get(pk=session_id)
    if session.status in TERMINAL_SESSION_STATUSES:
        if session.status == SessionStatus.MISSED:
            return session
        raise InvalidSessionStateError("Terminal sessions cannot be marked missed.")

    _set_terminal(session, status=SessionStatus.MISSED, outcome=SessionOutcome.MISSED)
    emit_session_missed(session_id=session.id)
    return session


@transaction.atomic
def mark_session_failed(*, session_id: uuid.UUID, reason: str = "") -> CommunicationSession:
    session = CommunicationSession.objects.select_for_update().get(pk=session_id)
    if session.status in TERMINAL_SESSION_STATUSES:
        if session.status == SessionStatus.FAILED:
            return session
        raise InvalidSessionStateError("Terminal sessions cannot be marked failed.")

    _set_terminal(session, status=SessionStatus.FAILED, outcome=SessionOutcome.FAILED)
    emit_session_failed(session_id=session.id, reason=reason)
    return session


@transaction.atomic
def record_call_attempt(*, session_id: uuid.UUID) -> CallAttempt:
    session = CommunicationSession.objects.select_for_update().get(pk=session_id)
    _ensure_not_terminal(session)

    attempt_number = session.call_attempts.count() + 1
    now = timezone.now()
    attempt = CallAttempt.objects.create(
        communication_session=session,
        attempt_number=attempt_number,
        started_at=now,
    )

    if session.status == SessionStatus.INITIATED:
        session.status = SessionStatus.CONNECTING
        update_fields = ["status", "updated_at"]
        bump_communication_session_version(session, update_fields)
        session.save(update_fields=update_fields)

    emit_call_attempt_started(
        attempt_id=attempt.id,
        session_id=session.id,
        attempt_number=attempt_number,
    )
    return attempt


@transaction.atomic
def report_attempt_result(
    *,
    attempt_id: uuid.UUID,
    outcome: str,
    failure_reason: str = "",
) -> CallAttempt:
    if outcome not in CallAttemptOutcome.values:
        raise InvalidSessionStateError("Invalid call attempt outcome.")

    attempt = CallAttempt.objects.select_for_update().select_related("communication_session").get(pk=attempt_id)
    session = CommunicationSession.objects.select_for_update().get(pk=attempt.communication_session_id)

    if attempt.outcome:
        return attempt

    now = timezone.now()
    attempt.outcome = outcome
    attempt.failure_reason = failure_reason
    attempt.ended_at = now
    attempt.save(update_fields=["outcome", "failure_reason", "ended_at"])

    if outcome == CallAttemptOutcome.CONNECTED:
        if session.status != SessionStatus.CONNECTED:
            session.status = SessionStatus.CONNECTED
            session.connected_at = now
            session.save(update_fields=["status", "connected_at", "updated_at"])
            emit_session_connected(session_id=session.id)
    elif outcome == CallAttemptOutcome.FAILED:
        emit_call_attempt_failed(attempt_id=attempt.id, session_id=session.id, reason=failure_reason)
    elif outcome == CallAttemptOutcome.DECLINED:
        _set_terminal(session, status=SessionStatus.DECLINED, outcome=SessionOutcome.DECLINED)
        emit_session_declined(session_id=session.id)
    elif outcome == CallAttemptOutcome.MISSED:
        _set_terminal(session, status=SessionStatus.MISSED, outcome=SessionOutcome.MISSED)
        emit_session_missed(session_id=session.id)

    return attempt


def get_call_attempt(attempt_id: uuid.UUID) -> CallAttempt:
    try:
        return CallAttempt.objects.get(pk=attempt_id)
    except CallAttempt.DoesNotExist as exc:
        raise CallAttemptNotFoundError("Call attempt not found.") from exc


def auto_cancel_unjoined_sessions(*, now: datetime | None = None, timeout_seconds: int | None = None) -> int:
    """Cancel sessions that never connected within the join timeout."""
    from django.conf import settings

    now = now or timezone.now()
    timeout = timeout_seconds if timeout_seconds is not None else int(
        getattr(settings, "COMMUNICATION_SESSION_JOIN_TIMEOUT_SECONDS", 120)
    )
    cutoff = now - timedelta(seconds=timeout)
    stale_ids = list(
        CommunicationSession.objects.filter(
            status__in=[SessionStatus.INITIATED, SessionStatus.CONNECTING],
            connected_at__isnull=True,
            initiated_at__lte=cutoff,
        ).values_list("id", flat=True)
    )
    cancelled = 0
    for session_id in stale_ids:
        cancel_session(session_id=session_id)
        cancelled += 1
    return cancelled
