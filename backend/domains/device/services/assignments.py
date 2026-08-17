"""Device assignment lifecycle."""

from __future__ import annotations

import uuid

from django.db import transaction
from django.utils import timezone

from domains.device.enums import AssignmentStatus, AssignmentType, DeviceOperationalStatus, PairingStatus
from domains.device.exceptions import AssignmentNotFoundError, EntitlementDeniedError, InvalidDeviceStateError
from domains.device.models import Device, DeviceAssignment
from domains.device.versioning import bump_device_version
from domains.identity_access.models import Elder
from domains.licensing.enums import EntitlementKey
from domains.licensing.services.entitlements import get_limit


def get_assignments(*, device_id: uuid.UUID | None = None, elder_id: uuid.UUID | None = None) -> list[DeviceAssignment]:
    queryset = DeviceAssignment.objects.select_related("device", "device__device_model", "elder").order_by(
        "-assigned_at"
    )
    if device_id is not None:
        queryset = queryset.filter(device_id=device_id)
    if elder_id is not None:
        queryset = queryset.filter(elder_id=elder_id)
    return list(queryset)


def _ensure_elder_exists(elder_id: uuid.UUID) -> Elder:
    try:
        return Elder.objects.get(pk=elder_id)
    except Elder.DoesNotExist as exc:
        raise InvalidDeviceStateError("Elder not found.") from exc


def _check_hub_entitlement(elder_id: uuid.UUID) -> None:
    limit = get_limit(elder_id, EntitlementKey.MAX_HUBS.value)
    if limit is None:
        raise EntitlementDeniedError("No active license entitlement for device assignment.")
    active_count = DeviceAssignment.objects.filter(
        elder_id=elder_id,
        status=AssignmentStatus.ASSIGNED,
    ).count()
    if active_count >= limit:
        raise EntitlementDeniedError("Elder has reached the maximum hub assignment limit.")


@transaction.atomic
def assign_device(
    *,
    device_id: uuid.UUID,
    elder_id: uuid.UUID,
    assignment_type: str,
) -> DeviceAssignment:
    if assignment_type not in AssignmentType.values:
        raise InvalidDeviceStateError("Invalid assignment type.")

    device = Device.objects.select_for_update().get(pk=device_id)
    _ensure_elder_exists(elder_id)
    _check_hub_entitlement(elder_id)

    active_assignment = DeviceAssignment.objects.filter(
        device=device,
        status=AssignmentStatus.ASSIGNED,
    ).first()
    if active_assignment is not None:
        raise InvalidDeviceStateError("Device is already assigned.")

    now = timezone.now()
    assignment = DeviceAssignment.objects.create(
        device=device,
        elder_id=elder_id,
        assignment_type=assignment_type,
        status=AssignmentStatus.ASSIGNED,
        assigned_at=now,
    )
    device.operational_status = DeviceOperationalStatus.ACTIVE
    device_fields = ["operational_status", "updated_at"]
    bump_device_version(device, device_fields)
    device.save(update_fields=device_fields)
    return assignment


@transaction.atomic
def return_device(*, device_id: uuid.UUID) -> DeviceAssignment:
    device = Device.objects.select_for_update().get(pk=device_id)
    assignment = DeviceAssignment.objects.filter(
        device=device,
        status=AssignmentStatus.ASSIGNED,
    ).first()
    if assignment is None:
        raise AssignmentNotFoundError("No active assignment found for this device.")

    now = timezone.now()
    assignment.status = AssignmentStatus.RETURNED
    assignment.unassigned_at = now
    assignment.save(update_fields=["status", "unassigned_at"])

    device.operational_status = DeviceOperationalStatus.INVENTORY
    device_fields = ["operational_status", "updated_at"]
    bump_device_version(device, device_fields)
    device.save(update_fields=device_fields)
    return assignment


@transaction.atomic
def refurbish_device(*, device_id: uuid.UUID) -> DeviceAssignment:
    device = Device.objects.select_for_update().get(pk=device_id)
    assignment = (
        DeviceAssignment.objects.filter(device=device)
        .order_by("-assigned_at")
        .first()
    )
    if assignment is None:
        raise AssignmentNotFoundError("No assignment history found for this device.")
    if assignment.status not in {AssignmentStatus.RETURNED, AssignmentStatus.REFURBISHED}:
        if assignment.status != AssignmentStatus.RETURNED:
            assignment.status = AssignmentStatus.RETURNED
            assignment.unassigned_at = assignment.unassigned_at or timezone.now()
            assignment.save(update_fields=["status", "unassigned_at"])

    refurbishment = DeviceAssignment.objects.create(
        device=device,
        elder=assignment.elder,
        assignment_type=assignment.assignment_type,
        status=AssignmentStatus.REFURBISHED,
        assigned_at=timezone.now(),
        unassigned_at=timezone.now(),
    )
    device.operational_status = DeviceOperationalStatus.INVENTORY
    device_fields = ["operational_status", "updated_at"]
    bump_device_version(device, device_fields)
    device.save(update_fields=device_fields)
    return refurbishment


def _device_kind(device_type: str) -> str:
    normalized = (device_type or "").upper()
    if normalized == "HUB":
        return "HUB"
    if normalized == "PILLBOX":
        return "PILLBOX"
    return "OTHER"


def _connectivity(current_state: dict, operational_status: str) -> str:
    network = current_state.get("network")
    if isinstance(network, str) and network.lower() in {"online", "offline"}:
        return network.lower()
    if operational_status == DeviceOperationalStatus.ACTIVE:
        return "unknown"
    return "offline"


def _battery_percent(current_state: dict) -> int | None:
    value = current_state.get("battery_percent", current_state.get("battery"))
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return int(value)


def list_elder_assigned_devices(*, elder_id: uuid.UUID) -> list[dict]:
    """Read-model of devices currently assigned to an Elder."""
    from domains.device.services.pairing import get_pairings

    _ensure_elder_exists(elder_id)
    items: list[dict] = []
    for assignment in get_assignments(elder_id=elder_id):
        if assignment.status != AssignmentStatus.ASSIGNED:
            continue
        device = assignment.device
        current_state = device.current_state or {}
        pairings = get_pairings(device_id=device.id)
        active_pairing = next((item for item in pairings if item.status == PairingStatus.ACTIVE), None)
        items.append(
            {
                "id": device.id,
                "kind": _device_kind(device.device_model.device_type),
                "serial_number": device.serial_number,
                "operational_status": device.operational_status,
                "last_seen_at": device.last_seen_at,
                "battery_percent": _battery_percent(current_state),
                "pairing_status": active_pairing.status if active_pairing is not None else None,
                "connectivity": _connectivity(current_state, device.operational_status),
                "assignment_type": assignment.assignment_type,
            }
        )
    return items
