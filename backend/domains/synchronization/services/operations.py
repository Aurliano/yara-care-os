"""Synchronization operations: delta/snapshot submit and internal apply."""

from __future__ import annotations

import uuid
from typing import Any

from django.db import transaction
from django.utils import timezone

from domains.synchronization.enums import (
    OperationStatus,
    OperationType,
    ReplicaHealth,
    ReplicaStatus,
    SessionStatus,
)
from domains.synchronization.exceptions import (
    IdempotencyConflictError,
    InvalidDeltaError,
    InvalidReplicaStateError,
    InvalidSessionStateError,
    OperationNotFoundError,
    SessionNotFoundError,
    SnapshotCorruptedError,
    SynchronizationConflictError,
    VersionMismatchError,
)
from domains.synchronization.identity import compute_payload_hash, compare_aggregate_versions
from domains.synchronization.models import ReplicaVersion, SynchronizationOperation, SynchronizationSession
from domains.synchronization.services.conflicts import detect_version_conflict, ensure_no_open_conflicts
from domains.synchronization.services.events import emit_delta_applied, emit_snapshot_applied
from domains.synchronization.services.replicas import advance_checkpoint
from domains.synchronization.services.sessions import (
    _complete_session,
    _transition_session,
)


def get_pending_operations(*, session_id: uuid.UUID) -> list[SynchronizationOperation]:
    return list(
        SynchronizationOperation.objects.filter(
            synchronization_session_id=session_id,
            status__in=[OperationStatus.PENDING, OperationStatus.VALIDATED],
        ).order_by("started_at")
    )


def _validate_payload_metadata(
    *,
    aggregate_reference: uuid.UUID,
    aggregate_version: str,
    payload: Any,
    payload_type: str,
    payload_hash: str,
) -> None:
    if not aggregate_reference:
        raise InvalidDeltaError("aggregate_reference is required.")
    if not aggregate_version:
        raise InvalidDeltaError("aggregate_version is required.")
    if not payload_type:
        raise InvalidDeltaError("payload_type is required.")
    if not payload_hash:
        raise InvalidDeltaError("payload_hash is required.")
    if compute_payload_hash(payload=payload) != payload_hash:
        raise InvalidDeltaError("payload_hash does not match payload.")


def _get_existing_operation(idempotency_key: str) -> SynchronizationOperation | None:
    return SynchronizationOperation.objects.filter(idempotency_key=idempotency_key).first()


def _assert_idempotent_submit(
    *,
    existing: SynchronizationOperation | None,
    aggregate_reference: uuid.UUID,
    aggregate_version: str,
    payload_hash: str,
    operation_type: str,
) -> SynchronizationOperation | None:
    if existing is None:
        return None
    if (
        existing.aggregate_reference != aggregate_reference
        or existing.aggregate_version != aggregate_version
        or existing.payload_hash != payload_hash
        or existing.operation_type != operation_type
    ):
        raise IdempotencyConflictError("Idempotency key reused with different payload.")
    return existing


def _ensure_snapshot_allowed(replica) -> None:
    allowed = (
        replica.checkpoint_sequence == 0
        or replica.health == ReplicaHealth.OUTDATED
        or replica.status in {ReplicaStatus.RESETTING, ReplicaStatus.OUTDATED}
    )
    if not allowed:
        raise InvalidReplicaStateError(
            "Snapshot synchronization is only allowed for first sync, recovery, reset, or corrupted replica."
        )


@transaction.atomic
def submit_aggregate_delta(
    *,
    session_id: uuid.UUID,
    aggregate_reference: uuid.UUID,
    aggregate_version: str,
    payload: Any,
    payload_type: str,
    payload_hash: str,
    idempotency_key: str,
    expected_version: str | None = None,
) -> SynchronizationOperation:
    _validate_payload_metadata(
        aggregate_reference=aggregate_reference,
        aggregate_version=aggregate_version,
        payload=payload,
        payload_type=payload_type,
        payload_hash=payload_hash,
    )

    existing = _assert_idempotent_submit(
        existing=_get_existing_operation(idempotency_key),
        aggregate_reference=aggregate_reference,
        aggregate_version=aggregate_version,
        payload_hash=payload_hash,
        operation_type=OperationType.DELTA,
    )
    if existing is not None:
        return existing

    session = SynchronizationSession.objects.select_for_update().select_related("replica_state").get(pk=session_id)
    if session.status in {SessionStatus.SESSION_COMPLETED, SessionStatus.CANCELLED}:
        raise InvalidSessionStateError("Cannot submit to a terminal session.")

    _transition_session(session, SessionStatus.PAYLOAD_RECEIVED)

    operation = SynchronizationOperation.objects.create(
        synchronization_session=session,
        operation_type=OperationType.DELTA,
        aggregate_reference=aggregate_reference,
        aggregate_version=aggregate_version,
        payload=payload,
        payload_type=payload_type,
        payload_hash=payload_hash,
        idempotency_key=idempotency_key,
        started_at=timezone.now(),
    )

    return apply_delta(operation_id=operation.id, expected_version=expected_version)


@transaction.atomic
def submit_aggregate_snapshot(
    *,
    session_id: uuid.UUID,
    aggregate_reference: uuid.UUID,
    aggregate_version: str,
    payload: Any,
    payload_type: str,
    payload_hash: str,
    idempotency_key: str,
) -> SynchronizationOperation:
    _validate_payload_metadata(
        aggregate_reference=aggregate_reference,
        aggregate_version=aggregate_version,
        payload=payload,
        payload_type=payload_type,
        payload_hash=payload_hash,
    )

    existing = _assert_idempotent_submit(
        existing=_get_existing_operation(idempotency_key),
        aggregate_reference=aggregate_reference,
        aggregate_version=aggregate_version,
        payload_hash=payload_hash,
        operation_type=OperationType.SNAPSHOT,
    )
    if existing is not None:
        return existing

    session = SynchronizationSession.objects.select_for_update().select_related("replica_state").get(pk=session_id)
    if session.status in {SessionStatus.SESSION_COMPLETED, SessionStatus.CANCELLED}:
        raise InvalidSessionStateError("Cannot submit to a terminal session.")

    _ensure_snapshot_allowed(session.replica_state)
    _transition_session(session, SessionStatus.PAYLOAD_RECEIVED)

    operation = SynchronizationOperation.objects.create(
        synchronization_session=session,
        operation_type=OperationType.SNAPSHOT,
        aggregate_reference=aggregate_reference,
        aggregate_version=aggregate_version,
        payload=payload,
        payload_type=payload_type,
        payload_hash=payload_hash,
        idempotency_key=idempotency_key,
        started_at=timezone.now(),
    )

    return apply_snapshot(operation_id=operation.id)


@transaction.atomic
def apply_delta(*, operation_id: uuid.UUID, expected_version: str | None = None) -> SynchronizationOperation:
    operation = (
        SynchronizationOperation.objects.select_for_update()
        .select_related("synchronization_session__replica_state")
        .get(pk=operation_id)
    )
    if operation.status == OperationStatus.APPLIED:
        return operation
    if operation.operation_type != OperationType.DELTA:
        raise InvalidDeltaError("Operation is not a delta.")

    session = SynchronizationSession.objects.select_for_update().get(pk=operation.synchronization_session_id)
    replica = session.replica_state

    _transition_session(session, SessionStatus.VALIDATION)
    ensure_no_open_conflicts(replica=replica, aggregate_reference=operation.aggregate_reference)

    conflict = detect_version_conflict(
        replica=replica,
        session=session,
        aggregate_reference=operation.aggregate_reference,
        incoming_version=operation.aggregate_version,
        expected_version=expected_version,
    )
    if conflict is not None:
        operation.status = OperationStatus.FAILED
        operation.failure_reason = conflict.conflict_type
        operation.save(update_fields=["status", "failure_reason"])
        raise SynchronizationConflictError("Version conflict detected.")

    current = ReplicaVersion.objects.filter(
        replica_state=replica,
        aggregate_reference=operation.aggregate_reference,
    ).first()
    if current is not None:
        comparison = compare_aggregate_versions(
            incoming=operation.aggregate_version,
            current=current.aggregate_version,
        )
        if comparison < 0:
            operation.status = OperationStatus.FAILED
            operation.failure_reason = "VERSION_MISMATCH"
            operation.save(update_fields=["status", "failure_reason"])
            raise VersionMismatchError("Incoming aggregate version is older than replica version.")

    operation.status = OperationStatus.VALIDATED
    operation.save(update_fields=["status"])

    ReplicaVersion.objects.update_or_create(
        replica_state=replica,
        aggregate_reference=operation.aggregate_reference,
        defaults={"aggregate_version": operation.aggregate_version},
    )

    operation.status = OperationStatus.APPLIED
    operation.applied_at = timezone.now()
    operation.save(update_fields=["status", "applied_at"])

    _transition_session(session, SessionStatus.CHANGES_APPLIED)
    advance_checkpoint(
        replica_identifier=replica.replica_identifier,
        checkpoint_token=session.synchronization_token,
    )
    _transition_session(session, SessionStatus.CHECKPOINT_ADVANCED)
    _complete_session(session)
    emit_delta_applied(
        operation_id=operation.id,
        session_id=session.id,
        aggregate_reference=operation.aggregate_reference,
    )
    return operation


@transaction.atomic
def apply_snapshot(*, operation_id: uuid.UUID) -> SynchronizationOperation:
    operation = (
        SynchronizationOperation.objects.select_for_update()
        .select_related("synchronization_session__replica_state")
        .get(pk=operation_id)
    )
    if operation.status == OperationStatus.APPLIED:
        return operation
    if operation.operation_type != OperationType.SNAPSHOT:
        raise SnapshotCorruptedError("Operation is not a snapshot.")

    if not isinstance(operation.payload, dict):
        raise SnapshotCorruptedError("Snapshot payload must be a JSON object.")

    session = SynchronizationSession.objects.select_for_update().get(pk=operation.synchronization_session_id)
    replica = session.replica_state

    _transition_session(session, SessionStatus.VALIDATION)
    ensure_no_open_conflicts(replica=replica, aggregate_reference=operation.aggregate_reference)

    operation.status = OperationStatus.VALIDATED
    operation.save(update_fields=["status"])

    ReplicaVersion.objects.update_or_create(
        replica_state=replica,
        aggregate_reference=operation.aggregate_reference,
        defaults={"aggregate_version": operation.aggregate_version},
    )

    operation.status = OperationStatus.APPLIED
    operation.applied_at = timezone.now()
    operation.save(update_fields=["status", "applied_at"])

    _transition_session(session, SessionStatus.CHANGES_APPLIED)
    advance_checkpoint(
        replica_identifier=replica.replica_identifier,
        checkpoint_token=session.synchronization_token,
    )
    _transition_session(session, SessionStatus.CHECKPOINT_ADVANCED)
    _complete_session(session)
    emit_snapshot_applied(
        operation_id=operation.id,
        session_id=session.id,
        aggregate_reference=operation.aggregate_reference,
    )
    return operation


def get_operation(operation_id: uuid.UUID) -> SynchronizationOperation:
    try:
        return SynchronizationOperation.objects.get(pk=operation_id)
    except SynchronizationOperation.DoesNotExist as exc:
        raise OperationNotFoundError("Synchronization operation not found.") from exc
