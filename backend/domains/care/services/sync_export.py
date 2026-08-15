"""Care-owned synchronization payload export."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import timedelta
from typing import Any

from django.utils import timezone

from domains.care.services.activities import get_care_activity
from domains.scheduling.models import Occurrence

INCREMENTAL_HORIZON_DAYS = 7


def _payload_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _epoch_millis(value) -> int:
    if value is None:
        return 0
    return int(value.timestamp() * 1000)


def _serialize_schedule(schedule) -> dict[str, Any]:
    return {
        "id": str(schedule.id),
        "owner_reference": schedule.owner_reference,
        "recurrence_definition_json": json.dumps(schedule.recurrence_definition),
        "timezone": schedule.timezone,
        "start_at_epoch_millis": _epoch_millis(schedule.start_at),
        "end_at_epoch_millis": _epoch_millis(schedule.end_at),
        "status": schedule.status,
        "updated_at_epoch_millis": _epoch_millis(schedule.updated_at),
    }


def _serialize_occurrence(occurrence: Occurrence) -> dict[str, Any]:
    return {
        "id": str(occurrence.id),
        "schedule_definition_id": str(occurrence.schedule_definition_id),
        "scheduled_for_epoch_millis": _epoch_millis(occurrence.scheduled_for),
        "status": occurrence.status,
        "updated_at_epoch_millis": _epoch_millis(occurrence.created_at),
    }


def build_care_activity_sync_delta(*, care_activity_id: uuid.UUID) -> dict[str, Any]:
    """Build opaque delta payload owned by Care for Synchronization submit."""
    activity = get_care_activity(care_activity_id)
    schedule = activity.schedule_definition
    horizon = timezone.now() + timedelta(days=INCREMENTAL_HORIZON_DAYS)
    occurrences = list(
        Occurrence.objects.filter(
            schedule_definition_id=schedule.id,
            scheduled_for__lte=horizon,
        ).order_by("scheduled_for")
    )
    payload = {
        "care_activity_id": str(activity.id),
        "elder_id": str(activity.elder_id),
        "activity_type": activity.activity_type,
        "status": activity.status,
        "display_title": activity.display_title,
        "display_subtitle": activity.display_subtitle,
        "schedule_definition_id": str(activity.schedule_definition_id),
        "workflow_definition_id": str(activity.workflow_definition_id),
        "aggregate_version": activity.aggregate_version,
        "schedule_definition": _serialize_schedule(schedule),
        "occurrences": [_serialize_occurrence(item) for item in occurrences],
    }
    return {
        "aggregate_reference": activity.id,
        "aggregate_version": str(activity.aggregate_version),
        "payload": payload,
        "payload_type": "care.activity.delta",
        "payload_hash": _payload_hash(payload),
    }
