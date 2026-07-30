"""Workflow event publication via the Event domain."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from django.utils import timezone

from domains.event.services.recording import EventInput, publish_event, record_event
from domains.workflow.identity import compute_workflow_event_id

EVENT_VERSION = 1
PRODUCER = "workflow"


def publish_workflow_fact(
    *,
    event_type: str,
    subject_id: uuid.UUID,
    occurred_at: datetime,
    payload: dict[str, Any],
    discriminator: str = "",
) -> None:
    event_id = compute_workflow_event_id(
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


def emit_execution_started(*, execution_id: uuid.UUID, occurrence_id: uuid.UUID, workflow_definition_id: uuid.UUID) -> None:
    publish_workflow_fact(
        event_type="ExecutionStarted",
        subject_id=execution_id,
        occurred_at=timezone.now(),
        payload={
            "workflow_execution_id": str(execution_id),
            "occurrence_id": str(occurrence_id),
            "workflow_definition_id": str(workflow_definition_id),
        },
    )


def emit_execution_confirmed(*, execution_id: uuid.UUID, occurred_at: datetime | None = None) -> None:
    publish_workflow_fact(
        event_type="ExecutionConfirmed",
        subject_id=execution_id,
        occurred_at=occurred_at or timezone.now(),
        payload={"workflow_execution_id": str(execution_id)},
    )


def emit_execution_missed(*, execution_id: uuid.UUID, occurred_at: datetime | None = None) -> None:
    publish_workflow_fact(
        event_type="ExecutionMissed",
        subject_id=execution_id,
        occurred_at=occurred_at or timezone.now(),
        payload={"workflow_execution_id": str(execution_id)},
    )


def emit_execution_postponed(*, execution_id: uuid.UUID, postpone_count: int) -> None:
    publish_workflow_fact(
        event_type="ExecutionPostponed",
        subject_id=execution_id,
        occurred_at=timezone.now(),
        discriminator=str(postpone_count),
        payload={
            "workflow_execution_id": str(execution_id),
            "postpone_count": postpone_count,
        },
    )


def emit_execution_cancelled(*, execution_id: uuid.UUID) -> None:
    publish_workflow_fact(
        event_type="ExecutionCancelled",
        subject_id=execution_id,
        occurred_at=timezone.now(),
        payload={"workflow_execution_id": str(execution_id)},
    )


def emit_execution_failed(*, execution_id: uuid.UUID, reason: str = "") -> None:
    publish_workflow_fact(
        event_type="ExecutionFailed",
        subject_id=execution_id,
        occurred_at=timezone.now(),
        payload={
            "workflow_execution_id": str(execution_id),
            "reason": reason,
        },
    )


def emit_escalation_triggered(*, execution_id: uuid.UUID, escalation_index: int, action_type: str) -> None:
    publish_workflow_fact(
        event_type="EscalationTriggered",
        subject_id=execution_id,
        occurred_at=timezone.now(),
        discriminator=str(escalation_index),
        payload={
            "workflow_execution_id": str(execution_id),
            "escalation_index": escalation_index,
            "action_type": action_type,
        },
    )
