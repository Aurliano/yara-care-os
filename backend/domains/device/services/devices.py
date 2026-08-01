"""Device aggregate commands and queries."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from django.db import transaction
from django.utils import timezone

from domains.device.enums import (
    CapabilityOverrideState,
    DeviceOperationalStatus,
)
from domains.device.exceptions import (
    CapabilityNotFoundError,
    DeviceNotFoundError,
    InvalidCapabilityOverrideError,
    InvalidDeviceStateError,
)
from domains.device.models import Device, DeviceCapability, DeviceCapabilityOverride
from domains.device.services.device_models import get_device_model, get_model_capability_codes
from domains.device.services.events import emit_device_offline, emit_device_online
from domains.device.versioning import bump_device_version


def get_device(device_id: uuid.UUID) -> Device:
    try:
        return Device.objects.select_related("device_model").get(pk=device_id)
    except Device.DoesNotExist as exc:
        raise DeviceNotFoundError("Device not found.") from exc


def get_device_state(device_id: uuid.UUID) -> dict[str, Any]:
    device = get_device(device_id)
    return {
        "device_id": str(device.id),
        "operational_status": device.operational_status,
        "current_state": device.current_state,
        "last_seen_at": device.last_seen_at.isoformat() if device.last_seen_at else None,
    }


@transaction.atomic
def create_device(
    *,
    device_model_id: uuid.UUID,
    serial_number: str,
    configuration: dict[str, Any] | None = None,
    current_state: dict[str, Any] | None = None,
) -> Device:
    device_model = get_device_model(device_model_id)
    device = Device.objects.create(
        device_model=device_model,
        serial_number=serial_number,
        operational_status=DeviceOperationalStatus.INVENTORY,
        configuration=configuration or {},
        current_state=current_state or {},
    )
    return device


@transaction.atomic
def update_device_state(
    *,
    device_id: uuid.UUID,
    current_state: dict[str, Any],
    is_online: bool | None = None,
) -> Device:
    device = Device.objects.select_for_update().get(pk=device_id)
    device.current_state = current_state
    device.last_seen_at = timezone.now()
    update_fields = ["current_state", "last_seen_at", "updated_at"]
    bump_device_version(device, update_fields)
    device.save(update_fields=update_fields)
    if is_online is True:
        emit_device_online(device_id=device.id)
    elif is_online is False:
        emit_device_offline(device_id=device.id)
    return device


@transaction.atomic
def add_capability_override(
    *,
    device_id: uuid.UUID,
    capability_code: str,
    state: str,
    reason: str,
    changed_by_user_id: uuid.UUID,
    effective_at: datetime | None = None,
) -> DeviceCapabilityOverride:
    if not reason.strip():
        raise InvalidCapabilityOverrideError("Override reason is mandatory.")

    device = get_device(device_id)
    model_codes = get_model_capability_codes(device.device_model)
    if capability_code not in model_codes:
        raise CapabilityNotFoundError("Capability is not defined on the device model.")

    if state not in CapabilityOverrideState.values:
        raise InvalidCapabilityOverrideError("Invalid override state.")

    capability = DeviceCapability.objects.get(code=capability_code)
    return DeviceCapabilityOverride.objects.create(
        device=device,
        capability=capability,
        state=state,
        reason=reason,
        changed_by_user_id=changed_by_user_id,
        effective_at=effective_at or timezone.now(),
    )


def get_effective_capability_state(device: Device, capability_code: str) -> str:
    model_codes = get_model_capability_codes(device.device_model)
    if capability_code not in model_codes:
        raise CapabilityNotFoundError("Capability is not defined on the device model.")

    override = (
        DeviceCapabilityOverride.objects.filter(
            device=device,
            capability__code=capability_code,
        )
        .order_by("-effective_at")
        .first()
    )
    if override is not None:
        return override.state
    return CapabilityOverrideState.ENABLED


def ensure_device_accepts_commands(device: Device) -> None:
    if device.operational_status in {DeviceOperationalStatus.INACTIVE, DeviceOperationalStatus.REVOKED}:
        raise InvalidDeviceStateError("Device cannot accept operational commands.")
