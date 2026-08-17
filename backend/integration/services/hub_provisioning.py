"""Hub device provisioning — backend is the sole authority for identity assignment.

Policy (see apps/hub/docs/PROVISIONING_POLICY.md):
- Device identity = serial_number (idempotent registration).
- Reinstall / factory reset on same hardware → same device_id and replica_identifier.
- Only revoke creates a new replica_identifier for the same device record.
"""

from __future__ import annotations

import uuid
from typing import Any

from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from domains.device.enums import AssignmentStatus, AssignmentType, DeviceOperationalStatus
from domains.device.exceptions import DeviceModelNotFoundError, DeviceNotFoundError, InvalidDeviceStateError
from domains.device.models import Device, DeviceAssignment, DeviceModel
from domains.device.services.assignments import assign_device, get_assignments
from domains.device.services.devices import create_device, get_device
from domains.identity_access.enums import MembershipStatus
from domains.identity_access.models import Membership
from domains.synchronization.enums import ReplicaType
from domains.synchronization.services.replicas import get_or_create_replica_state
from integration.exceptions import HubProvisioningError

PROVISIONING_CONFIG_KEY = "hub_provisioning"


def _provisioning_blob(device: Device) -> dict[str, Any]:
    return dict(device.configuration.get(PROVISIONING_CONFIG_KEY, {}))


def _save_provisioning(device: Device, blob: dict[str, Any]) -> None:
    configuration = dict(device.configuration)
    configuration[PROVISIONING_CONFIG_KEY] = blob
    device.configuration = configuration
    device.save(update_fields=["configuration", "updated_at"])


def _active_elder_id(device_id: uuid.UUID) -> uuid.UUID | None:
    assignment = (
        DeviceAssignment.objects.filter(
            device_id=device_id,
            status=AssignmentStatus.ASSIGNED,
        )
        .order_by("-assigned_at")
        .first()
    )
    return assignment.elder_id if assignment else None


def _device_model_by_code(device_model_code: str) -> DeviceModel:
    try:
        return DeviceModel.objects.get(model_code=device_model_code)
    except DeviceModel.DoesNotExist as exc:
        raise DeviceModelNotFoundError("Device model not found.") from exc


def _ensure_not_revoked(blob: dict[str, Any]) -> None:
    if blob.get("revoked"):
        raise HubProvisioningError("Hub provisioning has been revoked.")


def _primary_elder_id_for_user(user) -> uuid.UUID | None:
    membership = (
        Membership.objects.filter(user=user, status=MembershipStatus.ACTIVE)
        .order_by("-is_primary", "-joined_at")
        .first()
    )
    return membership.elder_id if membership else None


def _ensure_hub_assigned_to_caregiver_elder(*, device_id: uuid.UUID, user) -> uuid.UUID | None:
    active = _active_elder_id(device_id)
    if active is not None:
        return active
    elder_id = _primary_elder_id_for_user(user)
    if elder_id is None:
        return None
    existing = get_assignments(device_id=device_id)
    if any(item.status == AssignmentStatus.ASSIGNED for item in existing):
        return _active_elder_id(device_id)
    assign_device(
        device_id=device_id,
        elder_id=elder_id,
        assignment_type=AssignmentType.OWNED,
    )
    return elder_id


@transaction.atomic
def register_hub_device(*, serial_number: str, device_model_code: str) -> dict[str, Any]:
    """Register or restore a hub device. Backend assigns device_id and replica_identifier."""
    device_model = _device_model_by_code(device_model_code)
    device = Device.objects.select_for_update().filter(serial_number=serial_number).first()
    now = timezone.now()

    if device is None:
        device = create_device(
            device_model_id=device_model.id,
            serial_number=serial_number,
            current_state={"network": "registering"},
        )
        replica_identifier = uuid.uuid4()
        blob = {
            "replica_identifier": str(replica_identifier),
            "provisioned_at": now.isoformat(),
            "provisioning_state": "REGISTERED",
            "revoked": False,
        }
        _save_provisioning(device, blob)
    else:
        blob = _provisioning_blob(device)
        if not blob or blob.get("revoked"):
            replica_identifier = uuid.uuid4()
            blob = {
                "replica_identifier": str(replica_identifier),
                "provisioned_at": now.isoformat(),
                "provisioning_state": "REGISTERED",
                "revoked": False,
            }
            _save_provisioning(device, blob)
        else:
            replica_identifier = uuid.UUID(blob["replica_identifier"])

    get_or_create_replica_state(
        replica_identifier=replica_identifier,
        replica_type=ReplicaType.HUB,
    )
    device.operational_status = DeviceOperationalStatus.INVENTORY
    device.save(update_fields=["operational_status", "updated_at"])

    return {
        "device_id": str(device.id),
        "replica_identifier": str(replica_identifier),
        "provisioning_state": blob["provisioning_state"],
        "provisioned_at": blob["provisioned_at"],
        "elder_id": str(_active_elder_id(device.id)) if _active_elder_id(device.id) else None,
    }


@transaction.atomic
def authenticate_hub_device(
    *,
    device_id: uuid.UUID,
    phone: str,
    password: str,
) -> dict[str, Any]:
    """Authenticate a caregiver account and mark hub provisioning as READY."""
    try:
        device = Device.objects.select_for_update().get(pk=device_id)
    except Device.DoesNotExist as exc:
        raise DeviceNotFoundError("Device not found.") from exc

    blob = _provisioning_blob(device)
    if not blob:
        raise HubProvisioningError("Device is not registered for hub provisioning.")
    _ensure_not_revoked(blob)

    user = authenticate(username=phone, password=password)
    if user is None:
        raise HubProvisioningError("Invalid credentials.")

    elder_id = _ensure_hub_assigned_to_caregiver_elder(device_id=device.id, user=user)

    refresh = RefreshToken.for_user(user)
    now = timezone.now()
    blob["provisioning_state"] = "READY"
    blob["authenticated_at"] = now.isoformat()
    _save_provisioning(device, blob)

    if elder_id is None:
        elder_id = _active_elder_id(device.id)
    return {
        "device_id": str(device.id),
        "replica_identifier": blob["replica_identifier"],
        "provisioning_state": blob["provisioning_state"],
        "provisioned_at": blob["provisioned_at"],
        "authenticated_at": blob["authenticated_at"],
        "elder_id": str(elder_id) if elder_id else None,
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def get_hub_provisioning_status(*, device_id: uuid.UUID) -> dict[str, Any]:
    """Return persisted provisioning status for a hub device."""
    device = get_device(device_id)
    blob = _provisioning_blob(device)
    if not blob:
        return {
            "device_id": str(device.id),
            "replica_identifier": None,
            "provisioning_state": "UNPROVISIONED",
            "provisioned_at": None,
            "authenticated_at": None,
            "elder_id": None,
            "revoked": False,
        }

    elder_id = _active_elder_id(device.id)
    return {
        "device_id": str(device.id),
        "replica_identifier": blob.get("replica_identifier"),
        "provisioning_state": "REVOKED" if blob.get("revoked") else blob.get("provisioning_state", "REGISTERED"),
        "provisioned_at": blob.get("provisioned_at"),
        "authenticated_at": blob.get("authenticated_at"),
        "elder_id": str(elder_id) if elder_id else None,
        "revoked": bool(blob.get("revoked")),
    }


def get_assigned_hub_replica_identifier(*, elder_id: uuid.UUID) -> uuid.UUID | None:
    """Return the Hub replica for an elder's active DeviceAssignment, if provisioned."""
    for assignment in get_assignments(elder_id=elder_id):
        if assignment.status != AssignmentStatus.ASSIGNED:
            continue
        blob = _provisioning_blob(assignment.device)
        if blob.get("revoked"):
            continue
        raw = blob.get("replica_identifier")
        if raw:
            return uuid.UUID(str(raw))
    return None


@transaction.atomic
def revoke_hub_provisioning(*, device_id: uuid.UUID) -> dict[str, Any]:
    """Revoke hub provisioning for a device."""
    device = Device.objects.select_for_update().get(pk=device_id)
    blob = _provisioning_blob(device)
    if not blob:
        raise InvalidDeviceStateError("Device is not provisioned.")

    blob["revoked"] = True
    blob["provisioning_state"] = "REVOKED"
    blob["revoked_at"] = timezone.now().isoformat()
    _save_provisioning(device, blob)
    return get_hub_provisioning_status(device_id=device_id)
