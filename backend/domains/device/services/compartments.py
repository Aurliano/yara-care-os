"""Compartment and compartment assignment."""

from __future__ import annotations

import uuid

from django.db import transaction
from django.utils import timezone

from domains.device.enums import CompartmentAssignmentStatus, CompartmentStatus
from domains.device.exceptions import CompartmentAssignmentError, CompartmentNotFoundError
from domains.device.models import Compartment, CompartmentAssignment
from domains.device.services.devices import get_device
from domains.device.services.events import emit_compartment_closed, emit_compartment_opened


def get_compartments(*, device_id: uuid.UUID) -> list[Compartment]:
    return list(Compartment.objects.filter(device_id=device_id).order_by("number"))


def get_compartment(compartment_id: uuid.UUID) -> Compartment:
    try:
        return Compartment.objects.select_related("device").get(pk=compartment_id)
    except Compartment.DoesNotExist as exc:
        raise CompartmentNotFoundError("Compartment not found.") from exc


@transaction.atomic
def create_compartment(
    *,
    device_id: uuid.UUID,
    number: int,
    label: str = "",
) -> Compartment:
    get_device(device_id)
    return Compartment.objects.create(
        device_id=device_id,
        number=number,
        label=label,
        status=CompartmentStatus.ACTIVE,
    )


@transaction.atomic
def assign_compartment(
    *,
    compartment_id: uuid.UUID,
    care_activity_reference: uuid.UUID,
) -> CompartmentAssignment:
    compartment = Compartment.objects.select_for_update().get(pk=compartment_id)
    active = CompartmentAssignment.objects.filter(
        compartment=compartment,
        status=CompartmentAssignmentStatus.ACTIVE,
    ).first()
    if active is not None:
        raise CompartmentAssignmentError("Compartment already has an active assignment.")

    return CompartmentAssignment.objects.create(
        compartment=compartment,
        care_activity_reference=care_activity_reference,
        status=CompartmentAssignmentStatus.ACTIVE,
        assigned_at=timezone.now(),
    )


@transaction.atomic
def release_compartment_assignment(*, assignment_id: uuid.UUID) -> CompartmentAssignment:
    assignment = CompartmentAssignment.objects.select_for_update().get(pk=assignment_id)
    if assignment.status == CompartmentAssignmentStatus.RELEASED:
        return assignment
    assignment.status = CompartmentAssignmentStatus.RELEASED
    assignment.unassigned_at = timezone.now()
    assignment.save(update_fields=["status", "unassigned_at"])
    return assignment


@transaction.atomic
def record_compartment_opened(*, compartment_id: uuid.UUID) -> Compartment:
    compartment = get_compartment(compartment_id)
    emit_compartment_opened(compartment_id=compartment.id, device_id=compartment.device_id)
    return compartment


@transaction.atomic
def record_compartment_closed(*, compartment_id: uuid.UUID) -> Compartment:
    compartment = get_compartment(compartment_id)
    emit_compartment_closed(compartment_id=compartment.id, device_id=compartment.device_id)
    return compartment
