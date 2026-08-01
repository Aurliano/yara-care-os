"""Synchronization event publication via the Event domain."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from django.utils import timezone

from domains.event.services.recording import EventInput, publish_event, record_event
from domains.synchronization.identity import compute_synchronization_event_id

EVENT_VERSION = 1
PRODUCER = "synchronization"


def publish_synchronization_fact(
    *,
    event_type: str,
    subject_id: uuid.UUID,
    occurred_at: datetime,
    payload: dict[str, Any],
    discriminator: str = "",
) -> None:
    event_id = compute_synchronization_event_id(
        event_type=event_type,
        subject_id=subject_id,
        discriminator=discriminator,
    )
    event = record_event(
        EventInput(
            event_id=event_id,
            event_type=event_type,
            event_version=EVENT_VERSION,
            producer=PRODUCER,
            occurred_at=occurred_at,
            payload=payload,
        )
    )
    publish_event(event_id=event.id)


def emit_synchronization_started(*, session_id: uuid.UUID, replica_identifier: uuid.UUID) -> None:
    publish_synchronization_fact(
        event_type="SynchronizationStarted",
        subject_id=session_id,
        occurred_at=timezone.now(),
        payload={
            "synchronization_session_id": str(session_id),
            "replica_identifier": str(replica_identifier),
        },
    )


def emit_synchronization_completed(*, session_id: uuid.UUID) -> None:
    publish_synchronization_fact(
        event_type="SynchronizationCompleted",
        subject_id=session_id,
        occurred_at=timezone.now(),
        payload={"synchronization_session_id": str(session_id)},
    )


def emit_synchronization_cancelled(*, session_id: uuid.UUID) -> None:
    publish_synchronization_fact(
        event_type="SynchronizationCancelled",
        subject_id=session_id,
        occurred_at=timezone.now(),
        payload={"synchronization_session_id": str(session_id)},
    )


def emit_synchronization_failed(*, session_id: uuid.UUID, reason: str = "") -> None:
    publish_synchronization_fact(
        event_type="SynchronizationFailed",
        subject_id=session_id,
        occurred_at=timezone.now(),
        payload={
            "synchronization_session_id": str(session_id),
            "reason": reason,
        },
    )


def emit_replica_updated(
    *,
    replica_state_id: uuid.UUID,
    replica_identifier: uuid.UUID,
    discriminator: str = "",
) -> None:
    publish_synchronization_fact(
        event_type="ReplicaUpdated",
        subject_id=replica_state_id,
        occurred_at=timezone.now(),
        discriminator=discriminator,
        payload={
            "replica_state_id": str(replica_state_id),
            "replica_identifier": str(replica_identifier),
        },
    )


def emit_checkpoint_advanced(
    *,
    replica_state_id: uuid.UUID,
    checkpoint_sequence: int,
    checkpoint_token: uuid.UUID | None,
) -> None:
    publish_synchronization_fact(
        event_type="CheckpointAdvanced",
        subject_id=replica_state_id,
        occurred_at=timezone.now(),
        discriminator=str(checkpoint_sequence),
        payload={
            "replica_state_id": str(replica_state_id),
            "checkpoint_sequence": checkpoint_sequence,
            "checkpoint_token": str(checkpoint_token) if checkpoint_token else None,
        },
    )


def emit_conflict_detected(*, conflict_id: uuid.UUID, aggregate_reference: uuid.UUID, conflict_type: str) -> None:
    publish_synchronization_fact(
        event_type="ConflictDetected",
        subject_id=conflict_id,
        occurred_at=timezone.now(),
        payload={
            "synchronization_conflict_id": str(conflict_id),
            "aggregate_reference": str(aggregate_reference),
            "conflict_type": conflict_type,
        },
    )


def emit_conflict_resolved(*, conflict_id: uuid.UUID) -> None:
    publish_synchronization_fact(
        event_type="ConflictResolved",
        subject_id=conflict_id,
        occurred_at=timezone.now(),
        payload={"synchronization_conflict_id": str(conflict_id)},
    )


def emit_delta_applied(*, operation_id: uuid.UUID, session_id: uuid.UUID, aggregate_reference: uuid.UUID) -> None:
    publish_synchronization_fact(
        event_type="DeltaApplied",
        subject_id=operation_id,
        occurred_at=timezone.now(),
        payload={
            "synchronization_operation_id": str(operation_id),
            "synchronization_session_id": str(session_id),
            "aggregate_reference": str(aggregate_reference),
        },
    )


def emit_snapshot_applied(*, operation_id: uuid.UUID, session_id: uuid.UUID, aggregate_reference: uuid.UUID) -> None:
    publish_synchronization_fact(
        event_type="SnapshotApplied",
        subject_id=operation_id,
        occurred_at=timezone.now(),
        payload={
            "synchronization_operation_id": str(operation_id),
            "synchronization_session_id": str(session_id),
            "aggregate_reference": str(aggregate_reference),
        },
    )
