"""Communication-owned synchronization payload export."""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from domains.communication.services.sessions import get_session


def _payload_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_communication_session_sync_delta(*, session_id: uuid.UUID) -> dict[str, Any]:
    """Build opaque delta payload owned by Communication for Synchronization submit."""
    session = get_session(session_id)
    payload = {
        "communication_session_id": str(session.id),
        "elder_id": str(session.elder_id),
        "channel": session.channel,
        "status": session.status,
        "outcome": session.outcome,
        "external_execution_reference": (
            str(session.external_execution_reference) if session.external_execution_reference else None
        ),
        "aggregate_version": session.aggregate_version,
    }
    return {
        "aggregate_reference": session.id,
        "aggregate_version": str(session.aggregate_version),
        "payload": payload,
        "payload_type": "communication.session.delta",
        "payload_hash": _payload_hash(payload),
    }
