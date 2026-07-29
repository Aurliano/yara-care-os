"""Event domain models."""

from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone

from domains.event.enums import OutboxStatus
from domains.event.exceptions import EventImmutabilityError


class EventRecord(models.Model):
    """Immutable fact envelope recorded by the Event domain."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=128)
    event_version = models.PositiveIntegerField()
    producer = models.CharField(max_length=128)
    occurred_at = models.DateTimeField()
    recorded_at = models.DateTimeField(default=timezone.now, editable=False)
    correlation_id = models.CharField(max_length=128, blank=True, default="")
    causation_id = models.CharField(max_length=128, blank=True, default="")
    payload = models.JSONField(default=dict)

    class Meta:
        db_table = "event_record"
        indexes = [
            models.Index(fields=["correlation_id"], name="event_record_correlation_idx"),
            models.Index(fields=["producer"], name="event_record_producer_idx"),
            models.Index(fields=["occurred_at"], name="event_record_occurred_idx"),
        ]

    def save(self, *args, **kwargs) -> None:
        if self.pk and EventRecord.objects.filter(pk=self.pk).exists():
            raise EventImmutabilityError("Recorded events are immutable.")
        super().save(*args, **kwargs)

    @property
    def event_id(self) -> uuid.UUID:
        return self.id


class EventOutbox(models.Model):
    """Transactional outbox entry for reliable publication."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.OneToOneField(
        EventRecord,
        on_delete=models.CASCADE,
        related_name="outbox_entry",
    )
    status = models.CharField(
        max_length=16,
        choices=OutboxStatus.choices,
        default=OutboxStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "event_outbox"
        indexes = [
            models.Index(fields=["status", "created_at"], name="event_outbox_status_idx"),
        ]
