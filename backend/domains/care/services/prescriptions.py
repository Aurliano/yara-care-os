"""Prescription commands and queries."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from django.db import transaction

from domains.care.enums import CareActivityStatus, CareActivityType
from domains.care.exceptions import PrescriptionNotFoundError
from domains.care.models import Prescription
from domains.care.services.activities import create_care_activity, get_care_activity, update_care_activity
from domains.care.services.events import emit_prescription_created, emit_prescription_updated


def get_prescription(prescription_id: uuid.UUID) -> Prescription:
    try:
        return Prescription.objects.select_related(
            "care_activity",
            "care_activity__schedule_definition",
            "care_activity__workflow_definition",
        ).get(pk=prescription_id)
    except Prescription.DoesNotExist as exc:
        raise PrescriptionNotFoundError("Prescription not found.") from exc


def get_active_prescriptions(*, elder_id: uuid.UUID) -> list[Prescription]:
    return list(
        Prescription.objects.filter(
            care_activity__elder_id=elder_id,
            care_activity__status=CareActivityStatus.ACTIVE,
            care_activity__activity_type=CareActivityType.MEDICATION,
        )
        .select_related("care_activity")
        .order_by("care_activity__display_title")
    )


@transaction.atomic
def create_prescription(
    *,
    elder_id: uuid.UUID,
    workflow_definition_id: uuid.UUID,
    recurrence_definition: dict[str, Any],
    timezone_name: str,
    start_at: datetime,
    display_title: str,
    medication_reference: str,
    dosage_information: str,
    elder_friendly_description: str,
    end_at: datetime | None = None,
    display_subtitle: str = "",
    display_icon: str = "",
    confirmation_requirement: dict[str, Any] | None = None,
    compartment_assignment_reference: str = "",
    personalized_description: str = "",
    media_reference: uuid.UUID | None = None,
) -> Prescription:
    activity = create_care_activity(
        elder_id=elder_id,
        activity_type=CareActivityType.MEDICATION,
        workflow_definition_id=workflow_definition_id,
        recurrence_definition=recurrence_definition,
        timezone_name=timezone_name,
        start_at=start_at,
        end_at=end_at,
        display_title=display_title,
        display_subtitle=display_subtitle,
        display_icon=display_icon,
        confirmation_requirement=confirmation_requirement,
        compartment_assignment_reference=compartment_assignment_reference,
    )
    prescription = Prescription.objects.create(
        care_activity=activity,
        medication_reference=medication_reference,
        dosage_information=dosage_information,
        elder_friendly_description=elder_friendly_description,
        personalized_description=personalized_description,
        media_reference=media_reference,
    )
    emit_prescription_created(
        prescription_id=prescription.pk,
        care_activity_id=activity.id,
    )
    return prescription


@transaction.atomic
def update_prescription(
    prescription_id: uuid.UUID,
    *,
    medication_reference: str | None = None,
    dosage_information: str | None = None,
    elder_friendly_description: str | None = None,
    personalized_description: str | None = None,
    media_reference: uuid.UUID | None = None,
    display_title: str | None = None,
    display_subtitle: str | None = None,
    display_icon: str | None = None,
    confirmation_requirement: dict[str, Any] | None = None,
    compartment_assignment_reference: str | None = None,
    recurrence_definition: dict[str, Any] | None = None,
    timezone_name: str | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> Prescription:
    prescription = Prescription.objects.select_related("care_activity").select_for_update().get(
        pk=prescription_id
    )
    update_fields: list[str] = []
    if medication_reference is not None:
        prescription.medication_reference = medication_reference
        update_fields.append("medication_reference")
    if dosage_information is not None:
        prescription.dosage_information = dosage_information
        update_fields.append("dosage_information")
    if elder_friendly_description is not None:
        prescription.elder_friendly_description = elder_friendly_description
        update_fields.append("elder_friendly_description")
    if personalized_description is not None:
        prescription.personalized_description = personalized_description
        update_fields.append("personalized_description")
    if media_reference is not None:
        prescription.media_reference = media_reference
        update_fields.append("media_reference")
    if update_fields:
        prescription.save(update_fields=update_fields)

    update_care_activity(
        prescription.care_activity_id,
        display_title=display_title,
        display_subtitle=display_subtitle,
        display_icon=display_icon,
        confirmation_requirement=confirmation_requirement,
        compartment_assignment_reference=compartment_assignment_reference,
        recurrence_definition=recurrence_definition,
        timezone_name=timezone_name,
        start_at=start_at,
        end_at=end_at,
    )
    emit_prescription_updated(prescription_id=prescription.pk)
    return get_prescription(prescription_id)
