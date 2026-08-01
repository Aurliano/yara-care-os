"""Care-owned synchronization payload export."""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from domains.care.services.activities import get_care_activity


def _payload_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_care_activity_sync_delta(*, care_activity_id: uuid.UUID) -> dict[str, Any]:
    """Build opaque delta payload owned by Care for Synchronization submit."""
    activity = get_care_activity(care_activity_id)
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
    }
    return {
        "aggregate_reference": activity.id,
        "aggregate_version": str(activity.aggregate_version),
        "payload": payload,
        "payload_type": "care.activity.delta",
        "payload_hash": _payload_hash(payload),
    }
