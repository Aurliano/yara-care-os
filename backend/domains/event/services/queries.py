"""Event query interface."""

from __future__ import annotations

import uuid
from datetime import datetime

from domains.event.enums import OutboxStatus
from domains.event.models import EventOutbox, EventRecord


def get_event(event_id: uuid.UUID) -> EventRecord:
    return EventRecord.objects.get(pk=event_id)


def get_events_by_correlation(correlation_id: str) -> list[EventRecord]:
    if not correlation_id:
        return []
    return list(
        EventRecord.objects.filter(correlation_id=correlation_id).order_by("occurred_at", "recorded_at")
    )


def get_events_by_producer(producer: str) -> list[EventRecord]:
    return list(EventRecord.objects.filter(producer=producer).order_by("-occurred_at", "-recorded_at"))


def get_events_since(*, since: datetime) -> list[EventRecord]:
    return list(
        EventRecord.objects.filter(occurred_at__gte=since).order_by("occurred_at", "recorded_at")
    )


def list_recent_events(*, limit: int = 100) -> list[EventRecord]:
    return list(EventRecord.objects.order_by("recorded_at")[:limit])


def get_pending_outbox_count() -> int:
    return EventOutbox.objects.filter(status=OutboxStatus.PENDING).count()
