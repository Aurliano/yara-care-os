"""Event query interface."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from django.utils import timezone

from domains.event.enums import OutboxStatus
from domains.event.models import EventOutbox, EventRecord

DEFAULT_EVENT_QUERY_LIMIT = 100
MAX_EVENT_QUERY_LIMIT = 500


def _clamp_limit(limit: int | None) -> int:
    if limit is None:
        return DEFAULT_EVENT_QUERY_LIMIT
    return max(1, min(limit, MAX_EVENT_QUERY_LIMIT))


def get_event(event_id: uuid.UUID) -> EventRecord:
    return EventRecord.objects.get(pk=event_id)


def get_events_by_correlation(correlation_id: str, *, limit: int | None = None) -> list[EventRecord]:
    if not correlation_id:
        return []
    return list(
        EventRecord.objects.filter(correlation_id=correlation_id)
        .order_by("occurred_at", "recorded_at")[: _clamp_limit(limit)]
    )


def get_events_by_producer(producer: str, *, limit: int | None = None) -> list[EventRecord]:
    return list(
        EventRecord.objects.filter(producer=producer)
        .order_by("-occurred_at", "-recorded_at")[: _clamp_limit(limit)]
    )


def get_events_since(*, since: datetime, limit: int | None = None) -> list[EventRecord]:
    return list(
        EventRecord.objects.filter(occurred_at__gte=since)
        .order_by("occurred_at", "recorded_at")[: _clamp_limit(limit)]
    )


def list_recent_events(*, limit: int = 100) -> list[EventRecord]:
    return list(EventRecord.objects.order_by("recorded_at")[: _clamp_limit(limit)])


def get_pending_outbox_count() -> int:
    return EventOutbox.objects.filter(status=OutboxStatus.PENDING).count()


def count_stale_pending_outbox(*, older_than_minutes: int = 15) -> int:
    threshold = timezone.now() - timedelta(minutes=older_than_minutes)
    return EventOutbox.objects.filter(
        status=OutboxStatus.PENDING,
        created_at__lte=threshold,
    ).count()
