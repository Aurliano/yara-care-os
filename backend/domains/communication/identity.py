"""Deterministic Communication domain identity helpers."""

from __future__ import annotations

import uuid

from domains.communication.constants import COMMUNICATION_NAMESPACE


def compute_communication_event_id(
    *,
    event_type: str,
    subject_id: uuid.UUID,
    discriminator: str = "",
) -> uuid.UUID:
    key = f"{event_type}:{subject_id}"
    if discriminator:
        key = f"{key}:{discriminator}"
    return uuid.uuid5(COMMUNICATION_NAMESPACE, key)
