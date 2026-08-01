"""Device-owned synchronization payload export."""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from domains.device.services.devices import get_device


def _payload_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_device_sync_delta(*, device_id: uuid.UUID) -> dict[str, Any]:
    """Build opaque delta payload owned by Device for Synchronization submit."""
    device = get_device(device_id)
    payload = {
        "device_id": str(device.id),
        "operational_status": device.operational_status,
        "current_state": device.current_state,
        "aggregate_version": device.aggregate_version,
    }
    return {
        "aggregate_reference": device.id,
        "aggregate_version": str(device.aggregate_version),
        "payload": payload,
        "payload_type": "device.delta",
        "payload_hash": _payload_hash(payload),
    }
