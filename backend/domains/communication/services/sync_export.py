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


def build_contact_sync_delta(*, contact_id: uuid.UUID) -> dict[str, Any]:
    """Build opaque delta payload owned by Communication for Contact synchronization."""
    from domains.communication.models import Contact
    contact = Contact.objects.get(pk=contact_id)
    version = str(int(contact.updated_at.timestamp() * 1000))
    payload = {
        "id": str(contact.id),
        "elder_id": str(contact.elder_id),
        "display_name": contact.display_name,
        "phone": contact.phone,
        "communication_identities_json": json.dumps(contact.communication_identities),
        "preferred_channel": contact.preferred_channel,
        "photo_reference": str(contact.photo_reference) if contact.photo_reference else None,
        "is_priority": contact.is_priority,
        "status": contact.status,
        "updated_at_epoch_millis": int(contact.updated_at.timestamp() * 1000),
    }
    return {
        "aggregate_reference": contact.id,
        "aggregate_version": version,
        "payload": payload,
        "payload_type": "communication.contact.delta",
        "payload_hash": _payload_hash(payload),
    }

