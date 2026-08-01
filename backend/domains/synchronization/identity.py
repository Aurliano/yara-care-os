"""Deterministic Synchronization domain identity helpers."""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from domains.synchronization.constants import SYNCHRONIZATION_NAMESPACE


def compute_synchronization_event_id(
    *,
    event_type: str,
    subject_id: uuid.UUID,
    discriminator: str = "",
) -> uuid.UUID:
    key = f"{event_type}:{subject_id}"
    if discriminator:
        key = f"{key}:{discriminator}"
    return uuid.uuid5(SYNCHRONIZATION_NAMESPACE, key)


def compute_payload_hash(*, payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def compare_aggregate_versions(*, incoming: str, current: str) -> int:
    """Compare opaque aggregate versions. Returns -1, 0, or 1."""
    if incoming == current:
        return 0
    try:
        incoming_num = int(incoming)
        current_num = int(current)
    except ValueError:
        return -1 if incoming < current else 1
    return (incoming_num > current_num) - (incoming_num < current_num)
