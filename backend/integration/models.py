"""Integration runtime models."""

from __future__ import annotations

import uuid

from django.db import models


class ProcessedIntegrationEvent(models.Model):
    """Idempotency ledger: one row per (event, handler) pair.

    The same domain event may be consumed by multiple integration handlers in
    future; handler_name is the EVENT_HANDLERS registry key (event type).
    """

    id = models.BigAutoField(primary_key=True)
    event_id = models.UUIDField(db_index=True)
    handler_name = models.CharField(max_length=128)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "integration_processed_event"
        constraints = [
            models.UniqueConstraint(
                fields=["event_id", "handler_name"],
                name="integration_evt_handler_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["handler_name", "processed_at"], name="integration_evt_handler_idx"),
        ]
