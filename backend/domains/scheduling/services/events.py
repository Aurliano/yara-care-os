"""Scheduling event publication via the Event domain."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from django.utils import timezone

from domains.event.services.recording import EventInput, publish_event, record_event
from domains.scheduling.identity import compute_scheduling_event_id

EVENT_VERSION = 1
PRODUCER = "scheduling"


def publish_scheduling_fact(
    *,
    event_type: str,
    subject_id: uuid.UUID,
    occurred_at: datetime,
    payload: dict[str, Any],
    correlation_id: str = "",
    causation_id: str = "",
    discriminator: str = "",
) -> None:
    event_id = compute_scheduling_event_id(
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
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
    )
    publish_event(event_id=event.id)


def emit_schedule_created(*, schedule_id: uuid.UUID, owner_reference: str, timezone_name: str, status: str) -> None:
    publish_scheduling_fact(
        event_type="ScheduleCreated",
        subject_id=schedule_id,
        occurred_at=timezone.now(),
        payload={
            "schedule_definition_id": str(schedule_id),
            "owner_reference": owner_reference,
            "timezone": timezone_name,
            "status": status,
        },
    )


def emit_schedule_updated(*, schedule_id: uuid.UUID, status: str) -> None:
    occurred_at = timezone.now()
    publish_scheduling_fact(
        event_type="ScheduleUpdated",
        subject_id=schedule_id,
        occurred_at=occurred_at,
        discriminator=occurred_at.isoformat(),
        payload={
            "schedule_definition_id": str(schedule_id),
            "status": status,
        },
    )


def emit_schedule_paused(*, schedule_id: uuid.UUID) -> None:
    occurred_at = timezone.now()
    publish_scheduling_fact(
        event_type="SchedulePaused",
        subject_id=schedule_id,
        occurred_at=occurred_at,
        discriminator=occurred_at.isoformat(),
        payload={"schedule_definition_id": str(schedule_id)},
    )


def emit_schedule_resumed(*, schedule_id: uuid.UUID) -> None:
    occurred_at = timezone.now()
    publish_scheduling_fact(
        event_type="ScheduleResumed",
        subject_id=schedule_id,
        occurred_at=occurred_at,
        discriminator=occurred_at.isoformat(),
        payload={"schedule_definition_id": str(schedule_id)},
    )


def emit_schedule_cancelled(*, schedule_id: uuid.UUID) -> None:
    publish_scheduling_fact(
        event_type="ScheduleCancelled",
        subject_id=schedule_id,
        occurred_at=timezone.now(),
        payload={"schedule_definition_id": str(schedule_id)},
    )


def emit_occurrence_scheduled(
    *,
    occurrence_id: uuid.UUID,
    schedule_definition_id: uuid.UUID,
    scheduled_for: datetime,
) -> None:
    publish_scheduling_fact(
        event_type="OccurrenceScheduled",
        subject_id=occurrence_id,
        occurred_at=timezone.now(),
        payload={
            "occurrence_id": str(occurrence_id),
            "schedule_definition_id": str(schedule_definition_id),
            "scheduled_for": scheduled_for.isoformat(),
        },
    )


def emit_occurrence_due(
    *,
    occurrence_id: uuid.UUID,
    schedule_definition_id: uuid.UUID,
    scheduled_for: datetime,
    occurred_at: datetime,
) -> None:
    publish_scheduling_fact(
        event_type="OccurrenceDue",
        subject_id=occurrence_id,
        occurred_at=occurred_at,
        payload={
            "occurrence_id": str(occurrence_id),
            "schedule_definition_id": str(schedule_definition_id),
            "scheduled_for": scheduled_for.isoformat(),
        },
    )


def emit_occurrence_skipped(
    *,
    occurrence_id: uuid.UUID,
    schedule_definition_id: uuid.UUID,
    scheduled_for: datetime,
) -> None:
    publish_scheduling_fact(
        event_type="OccurrenceSkipped",
        subject_id=occurrence_id,
        occurred_at=timezone.now(),
        payload={
            "occurrence_id": str(occurrence_id),
            "schedule_definition_id": str(schedule_definition_id),
            "scheduled_for": scheduled_for.isoformat(),
        },
    )


def emit_occurrence_cancelled(
    *,
    occurrence_id: uuid.UUID,
    schedule_definition_id: uuid.UUID,
    scheduled_for: datetime,
) -> None:
    publish_scheduling_fact(
        event_type="OccurrenceCancelled",
        subject_id=occurrence_id,
        occurred_at=timezone.now(),
        payload={
            "occurrence_id": str(occurrence_id),
            "schedule_definition_id": str(schedule_definition_id),
            "scheduled_for": scheduled_for.isoformat(),
        },
    )
