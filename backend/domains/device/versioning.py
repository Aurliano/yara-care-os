"""Device aggregate version ownership for synchronization."""

from __future__ import annotations

from domains.device.models import Device


def bump_device_version(device: Device, update_fields: list[str]) -> list[str]:
    """Increment monotonic aggregate version owned by Device."""
    device.aggregate_version += 1
    if "aggregate_version" not in update_fields:
        update_fields.append("aggregate_version")
    return update_fields
