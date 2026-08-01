"""Hub ↔ Peripheral pairing lifecycle."""

from __future__ import annotations

import uuid

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from domains.device.enums import DeviceCapabilityCode, PairingStatus
from domains.device.exceptions import InvalidDeviceStateError, PairingNotFoundError
from domains.device.models import Pairing
from domains.device.services.devices import get_device, get_effective_capability_state
from domains.device.services.events import emit_device_paired


def get_pairings(*, device_id: uuid.UUID | None = None) -> list[Pairing]:
    queryset = Pairing.objects.select_related("hub_device", "peripheral_device").order_by("-created_at")
    if device_id is not None:
        queryset = queryset.filter(Q(hub_device_id=device_id) | Q(peripheral_device_id=device_id))
    return list(queryset)


def _ensure_ble_capable(device_id: uuid.UUID) -> None:
    device = get_device(device_id)
    state = get_effective_capability_state(device, DeviceCapabilityCode.BLE)
    if state != "ENABLED":
        raise InvalidDeviceStateError("Device does not have BLE capability enabled.")


@transaction.atomic
def create_pairing(*, hub_device_id: uuid.UUID, peripheral_device_id: uuid.UUID) -> Pairing:
    if hub_device_id == peripheral_device_id:
        raise InvalidDeviceStateError("Hub and peripheral must be different devices.")

    _ensure_ble_capable(hub_device_id)
    _ensure_ble_capable(peripheral_device_id)

    existing = Pairing.objects.filter(
        hub_device_id=hub_device_id,
        peripheral_device_id=peripheral_device_id,
        status__in={PairingStatus.PAIRING, PairingStatus.ACTIVE, PairingStatus.DISCONNECTED},
    ).first()
    if existing is not None:
        return existing

    return Pairing.objects.create(
        hub_device_id=hub_device_id,
        peripheral_device_id=peripheral_device_id,
        status=PairingStatus.PAIRING,
    )


@transaction.atomic
def activate_pairing(*, pairing_id: uuid.UUID) -> Pairing:
    pairing = Pairing.objects.select_for_update().get(pk=pairing_id)
    if pairing.status != PairingStatus.PAIRING:
        if pairing.status == PairingStatus.ACTIVE:
            return pairing
        raise InvalidDeviceStateError("Only pairing-in-progress records can be activated.")

    now = timezone.now()
    pairing.status = PairingStatus.ACTIVE
    pairing.paired_at = now
    pairing.save(update_fields=["status", "paired_at", "updated_at"])
    emit_device_paired(
        pairing_id=pairing.id,
        hub_device_id=pairing.hub_device_id,
        peripheral_device_id=pairing.peripheral_device_id,
    )
    return pairing


@transaction.atomic
def disconnect_pairing(*, pairing_id: uuid.UUID) -> Pairing:
    pairing = Pairing.objects.select_for_update().get(pk=pairing_id)
    if pairing.status == PairingStatus.REVOKED:
        return pairing
    if pairing.status not in {PairingStatus.ACTIVE, PairingStatus.DISCONNECTED}:
        raise InvalidDeviceStateError("Only active pairings can be disconnected.")

    pairing.status = PairingStatus.DISCONNECTED
    pairing.save(update_fields=["status", "updated_at"])
    return pairing


@transaction.atomic
def revoke_pairing(*, pairing_id: uuid.UUID) -> Pairing:
    pairing = Pairing.objects.select_for_update().get(pk=pairing_id)
    if pairing.status == PairingStatus.REVOKED:
        return pairing

    now = timezone.now()
    pairing.status = PairingStatus.REVOKED
    pairing.ended_at = now
    pairing.save(update_fields=["status", "ended_at", "updated_at"])
    return pairing


def get_pairing(pairing_id: uuid.UUID) -> Pairing:
    try:
        return Pairing.objects.select_related("hub_device", "peripheral_device").get(pk=pairing_id)
    except Pairing.DoesNotExist as exc:
        raise PairingNotFoundError("Pairing not found.") from exc
