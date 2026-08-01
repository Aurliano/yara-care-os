"""Device assignment lifecycle."""

from __future__ import annotations

import uuid

from django.db import transaction
from django.utils import timezone

from domains.device.enums import AssignmentStatus, AssignmentType, DeviceOperationalStatus
from domains.device.exceptions import AssignmentNotFoundError, EntitlementDeniedError, InvalidDeviceStateError
from domains.device.models import Device, DeviceAssignment
from domains.device.versioning import bump_device_version
from domains.identity_access.models import Elder
from domains.licensing.enums import EntitlementKey
from domains.licensing.services.entitlements import get_limit


def get_assignments(*, device_id: uuid.UUID | None = None, elder_id: uuid.UUID | None = None) -> list[DeviceAssignment]:
    queryset = DeviceAssignment.objects.select_related("device", "elder").order_by("-assigned_at")
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
