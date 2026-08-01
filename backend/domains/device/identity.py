"""Deterministic Device domain identity helpers."""

from __future__ import annotations

import uuid

from domains.device.constants import DEVICE_NAMESPACE


def compute_device_event_id(
    *,
    event_type: str,
    subject_id: uuid.UUID,
    discriminator: str = "",
) -> uuid.UUID:
    key = f"{event_type}:{subject_id}"
    if discriminator:
        key = f"{key}:{discriminator}"
    return uuid.uuid5(DEVICE_NAMESPACE, key)


def compute_command_id(*, idempotency_key: str) -> uuid.UUID:
    """Stable DeviceCommand identity for Hub retry-safe execution."""
    return uuid.uuid5(DEVICE_NAMESPACE, f"command:{idempotency_key}")
