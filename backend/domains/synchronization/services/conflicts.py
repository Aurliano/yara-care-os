"""Synchronization conflict detection and resolution."""

from __future__ import annotations

import uuid
from typing import Any

from django.db import transaction
from django.utils import timezone

from domains.synchronization.enums import ConflictStatus, ConflictType
from domains.synchronization.exceptions import ConflictNotFoundError, InvalidReplicaStateError, SynchronizationConflictError
from domains.synchronization.identity import compare_aggregate_versions
from domains.synchronization.models import ReplicaState, ReplicaVersion, SynchronizationConflict, SynchronizationSession
from domains.synchronization.services.events import emit_conflict_detected, emit_conflict_resolved
from domains.synchronization.services.replicas import advance_checkpoint, get_replica_state


def get_conflicts(*, replica_identifier: uuid.UUID, include_resolved: bool = False) -> list[SynchronizationConflict]:
    replica = get_replica_state(replica_identifier=replica_identifier)
    queryset = SynchronizationConflict.objects.filter(replica_state=replica)
    if not include_resolved:
        queryset = queryset.filter(status=ConflictStatus.OPEN)
    return list(queryset.order_by("-detected_at"))


def get_conflict(conflict_id: uuid.UUID) -> SynchronizationConflict:
    try:
        return SynchronizationConflict.objects.get(pk=conflict_id)
    except SynchronizationConflict.DoesNotExist as exc:
        raise ConflictNotFoundError("Synchronization conflict not found.") from exc


@transaction.atomic
def record_conflict(
    *,
    replica: ReplicaState,
    session: SynchronizationSession | None,
    aggregate_reference: uuid.UUID,
    conflict_type: str,
    local_version: str = "",
    remote_version: str = "",
) -> SynchronizationConflict:
    conflict = SynchronizationConflict.objects.create(
        replica_state=replica,
        synchronization_session=session,
        aggregate_reference=aggregate_reference,
        conflict_type=conflict_type,
        local_version=local_version,
        remote_version=remote_version,
        detected_at=timezone.now(),
    )
    emit_conflict_detected(
        conflict_id=conflict.id,
        aggregate_reference=aggregate_reference,
        conflict_type=conflict_type,
    )
    return conflict


def detect_version_conflict(
    *,
    replica: ReplicaState,
    session: SynchronizationSession | None,
    aggregate_reference: uuid.UUID,
    incoming_version: str,
    expected_version: str | None = None,
) -> SynchronizationConflict | None:
    current = ReplicaVersion.objects.filter(
        replica_state=replica,
        aggregate_reference=aggregate_reference,
    ).first()

    if expected_version is not None and incoming_version != expected_version:
        return record_conflict(
            replica=replica,
            session=session,
            aggregate_reference=aggregate_reference,
            conflict_type=ConflictType.VERSION_MISMATCH,
            local_version=current.aggregate_version if current else "",
            remote_version=incoming_version,
        )

    if current is None:
        return None

    comparison = compare_aggregate_versions(incoming=incoming_version, current=current.aggregate_version)
    if comparison < 0:
        return record_conflict(
            replica=replica,
            session=session,
            aggregate_reference=aggregate_reference,
            conflict_type=ConflictType.VERSION_MISMATCH,
            local_version=current.aggregate_version,
            remote_version=incoming_version,
        )
    if comparison == 0:
        return None

    if expected_version is None:
        return record_conflict(
            replica=replica,
            session=session,
            aggregate_reference=aggregate_reference,
            conflict_type=ConflictType.CONCURRENT_CHANGE,
            local_version=current.aggregate_version,
            remote_version=incoming_version,
        )
    return None


def detect_checkpoint_conflict(
    *,
    replica: ReplicaState,
    session: SynchronizationSession,
    expected_checkpoint_sequence: int,
) -> SynchronizationConflict | None:
    if replica.checkpoint_sequence != expected_checkpoint_sequence:
        return record_conflict(
            replica=replica,
            session=session,
            aggregate_reference=session.id,
            conflict_type=ConflictType.CHECKPOINT_MISMATCH,
            local_version=str(replica.checkpoint_sequence),
            remote_version=str(expected_checkpoint_sequence),
        )
    return None


def apply_resolution_payload(
    *,
    replica_state_id: uuid.UUID,
    aggregate_reference: uuid.UUID,
    resolution_payload: dict[str, Any],
) -> None:
    resolved_version = str(resolution_payload.get("aggregate_version", ""))
    if not resolved_version:
        raise InvalidReplicaStateError("Resolution payload must include aggregate_version.")
    ReplicaVersion.objects.update_or_create(
        replica_state_id=replica_state_id,
        aggregate_reference=aggregate_reference,
        defaults={"aggregate_version": resolved_version},
    )


@transaction.atomic
def resolve_conflict(
    *,
    conflict_id: uuid.UUID,
    resolution_payload: dict[str, Any],
) -> SynchronizationConflict:
    conflict = SynchronizationConflict.objects.select_for_update().get(pk=conflict_id)
    if conflict.status == ConflictStatus.RESOLVED:
        return conflict

    if not resolution_payload:
        raise InvalidReplicaStateError("Resolution payload is required.")

    apply_resolution_payload(
        replica_state_id=conflict.replica_state_id,
        aggregate_reference=conflict.aggregate_reference,
        resolution_payload=resolution_payload,
    )

    conflict.status = ConflictStatus.RESOLVED
    conflict.resolution_payload = resolution_payload
    conflict.resolved_at = timezone.now()
    conflict.save(update_fields=["status", "resolution_payload", "resolved_at"])

    advance_checkpoint(replica_identifier=conflict.replica_state.replica_identifier)
    emit_conflict_resolved(conflict_id=conflict.id)
    return conflict


def ensure_no_open_conflicts(*, replica: ReplicaState, aggregate_reference: uuid.UUID) -> None:
    if SynchronizationConflict.objects.filter(
        replica_state=replica,
        aggregate_reference=aggregate_reference,
        status=ConflictStatus.OPEN,
    ).exists():
        raise SynchronizationConflictError("Open synchronization conflict exists for aggregate.")
