"""Event recording and publication."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from django.db import IntegrityError, transaction
from django.utils import timezone

from domains.event.enums import OutboxStatus
from domains.event.exceptions import DuplicateEventError
from domains.event.models import EventOutbox, EventRecord


@dataclass(frozen=True, slots=True)
class EventInput:
    event_id: uuid.UUID
    event_type: str
    event_version: int
    producer: str
    occurred_at: datetime
    payload: dict[str, Any]
    correlation_id: str = ""
    causation_id: str = ""


def _event_matches(existing: EventRecord, event_input: EventInput) -> bool:
    return (
        existing.event_type == event_input.event_type
        and existing.event_version == event_input.event_version
        and existing.producer == event_input.producer
        and existing.occurred_at == event_input.occurred_at
        and existing.correlation_id == event_input.correlation_id
        and existing.causation_id == event_input.causation_id
        and existing.payload == event_input.payload
    )


@transaction.atomic
def record_event(event_input: EventInput) -> EventRecord:
    """Record an immutable event fact and enqueue it for publication."""
    existing = EventRecord.objects.filter(pk=event_input.event_id).first()
    if existing is not None:
        if not _event_matches(existing, event_input):
            raise DuplicateEventError("event_id already exists with different event data.")
        return existing

    try:
        event = EventRecord.objects.create(
            id=event_input.event_id,
            event_type=event_input.event_type,
            event_version=event_input.event_version,
            producer=event_input.producer,
            occurred_at=event_input.occurred_at,
            recorded_at=timezone.now(),
            correlation_id=event_input.correlation_id,
            causation_id=event_input.causation_id,
            payload=event_input.payload,
        )
        EventOutbox.objects.create(event=event, status=OutboxStatus.PENDING)
    except IntegrityError as exc:
        existing = EventRecord.objects.get(pk=event_input.event_id)
        if not _event_matches(existing, event_input):
            raise DuplicateEventError("event_id already exists with different event data.") from exc
        return existing

    return event


@transaction.atomic
def publish_event(*, event_id: uuid.UUID) -> EventOutbox:
    """Mark a recorded event as published. Idempotent for repeated calls."""
    outbox = (
        EventOutbox.objects.select_for_update()
        .select_related("event")
        .get(event_id=event_id)
    )
    if outbox.status == OutboxStatus.PUBLISHED:
        return outbox

    outbox.status = OutboxStatus.PUBLISHED
    outbox.published_at = timezone.now()
    outbox.save(update_fields=["status", "published_at"])
    return outbox
