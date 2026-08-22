"""Notification domain models."""

from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone

from domains.notification.enums import AlertSeverity


class CaregiverAlert(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    elder = models.ForeignKey(
        "identity_access.Elder",
        on_delete=models.PROTECT,
        related_name="caregiver_alerts",
    )
    title = models.CharField(max_length=160)
    body = models.CharField(max_length=400)
    severity = models.CharField(max_length=16, choices=AlertSeverity.choices)
    occurred_at = models.DateTimeField()
    source_type = models.CharField(max_length=64)
    source_reference = models.CharField(max_length=128)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "caregiver_alert"
        indexes = [
            models.Index(fields=["elder", "-occurred_at"], name="caregiver_alert_elder_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["source_type", "source_reference"],
                name="caregiver_alert_source_idempotent",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.elder_id}:{self.source_type}"
