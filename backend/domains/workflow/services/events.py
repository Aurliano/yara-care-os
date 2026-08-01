"""Workflow event publication via the Event domain."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from django.utils import timezone

from common.observability.logging import log_structured
from common.observability.metrics import increment
from domains.event.services.recording import EventInput, publish_event, record_event
from domains.workflow.identity import compute_workflow_event_id

EVENT_VERSION = 1
PRODUCER = "workflow"
logger = logging.getLogger("yara.workflow")

_WORKFLOW_METRICS = {
    "ExecutionStarted": "workflow.started",
    "ExecutionConfirmed": "workflow.confirmed",
    "ExecutionMissed": "workflow.missed",
}


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
    metric = _WORKFLOW_METRICS.get(event_type)
    if metric:
        increment(metric)
    log_structured(
        logger,
        "workflow.event.published",
        event_id=event.id,
        execution_id=subject_id if event_type.startswith("Execution") else None,
        correlation_id=event.correlation_id or None,
        event_type=event_type,
    )


def emit_execution_started(
    *,
    execution_id: uuid.UUID,
    occurrence_id: uuid.UUID,
    workflow_definition_id: uuid.UUID,
    schedule_definition_id: uuid.UUID,
    current_action: dict[str, Any],
    current_step: str,
    dispatch_context: dict[str, Any] | None = None,
) -> None:
    publish_workflow_fact(
        event_type="ExecutionStarted",
        subject_id=execution_id,
        occurred_at=timezone.now(),
        payload={
            "workflow_execution_id": str(execution_id),
            "occurrence_id": str(occurrence_id),
            "workflow_definition_id": str(workflow_definition_id),
            "schedule_definition_id": str(schedule_definition_id),
            "current_action": current_action,
            "current_step": current_step,
            "dispatch_context": dispatch_context or {},
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


def emit_escalation_triggered(
    *,
    execution_id: uuid.UUID,
    escalation_index: int,
    action_type: str,
    action: dict[str, Any],
    dispatch_context: dict[str, Any] | None = None,
) -> None:
    publish_workflow_fact(
        event_type="EscalationTriggered",
        subject_id=execution_id,
        occurred_at=timezone.now(),
        discriminator=str(escalation_index),
        payload={
            "workflow_execution_id": str(execution_id),
            "escalation_index": escalation_index,
            "action_type": action_type,
            "action": action,
            "dispatch_context": dispatch_context or {},
        },
    )
