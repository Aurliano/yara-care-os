"""Care activity commands and queries."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from django.db import transaction

from domains.care.enums import CareActivityStatus, CareActivityType
from domains.care.exceptions import CareActivityNotFoundError, ElderNotFoundError, InvalidCareActivityStateError
from domains.care.models import CareActivity
from domains.care.services.events import (
    emit_care_activity_created,
    emit_care_activity_ended,
    emit_care_activity_paused,
    emit_care_activity_resumed,
    emit_care_activity_updated,
)
from domains.care.versioning import bump_care_activity_version
from domains.identity_access.models import Elder
from domains.scheduling.services.schedules import (
    cancel_schedule,
    create_schedule,
    pause_schedule,
    resume_schedule,
    update_schedule,
)
from domains.workflow.services.executions import get_workflow_definition


def _ensure_elder_exists(elder_id: uuid.UUID) -> Elder:
    try:
        return Elder.objects.get(pk=elder_id)
    except Elder.DoesNotExist as exc:
        raise ElderNotFoundError("Elder not found.") from exc


def get_care_activity(care_activity_id: uuid.UUID) -> CareActivity:
    try:
        return CareActivity.objects.select_related(
            "schedule_definition",
            "workflow_definition",
            "prescription",
        ).get(pk=care_activity_id)
    except CareActivity.DoesNotExist as exc:
        raise CareActivityNotFoundError("Care activity not found.") from exc


def get_care_activity_for_schedule(schedule_definition_id: uuid.UUID) -> CareActivity:
    try:
        return CareActivity.objects.select_related("workflow_definition").get(
            schedule_definition_id=schedule_definition_id
        )
    except CareActivity.DoesNotExist as exc:
        raise CareActivityNotFoundError("No care activity is linked to this schedule.") from exc


def get_elder_care_activities(*, elder_id: uuid.UUID, status: str | None = None) -> list[CareActivity]:
    queryset = CareActivity.objects.filter(elder_id=elder_id).select_related(
        "schedule_definition",
        "workflow_definition",
    )
    if status is not None:
        queryset = queryset.filter(status=status)
    return list(queryset.order_by("-created_at"))


def get_care_activity_status(care_activity_id: uuid.UUID) -> dict[str, Any]:
    activity = get_care_activity(care_activity_id)
    return {
        "care_activity_id": str(activity.id),
        "status": activity.status,
        "activity_type": activity.activity_type,
        "schedule_definition_id": str(activity.schedule_definition_id),
        "workflow_definition_id": str(activity.workflow_definition_id),
    }


@transaction.atomic
def create_care_activity(
    *,
    elder_id: uuid.UUID,
    activity_type: str,
    workflow_definition_id: uuid.UUID,
    recurrence_definition: dict[str, Any],
    timezone_name: str,
    start_at: datetime,
    display_title: str,
    end_at: datetime | None = None,
    display_subtitle: str = "",
    display_icon: str = "",
    confirmation_requirement: dict[str, Any] | None = None,
    compartment_assignment_reference: str = "",
) -> CareActivity:
    _ensure_elder_exists(elder_id)
    get_workflow_definition(workflow_definition_id)

    if activity_type not in CareActivityType.values:
        raise InvalidCareActivityStateError("Invalid activity type.")

    activity_id = uuid.uuid4()
    schedule = create_schedule(
        owner_reference=f"care_activity:{activity_id}",
        recurrence_definition=recurrence_definition,
        timezone_name=timezone_name,
        start_at=start_at,
        end_at=end_at,
    )

    activity = CareActivity.objects.create(
        id=activity_id,
        elder_id=elder_id,
        activity_type=activity_type,
        status=CareActivityStatus.ACTIVE,
        schedule_definition=schedule,
        workflow_definition_id=workflow_definition_id,
        display_title=display_title,
        display_subtitle=display_subtitle,
        display_icon=display_icon,
        confirmation_requirement=confirmation_requirement or {},
        compartment_assignment_reference=compartment_assignment_reference,
    )
    emit_care_activity_created(
        care_activity_id=activity.id,
        elder_id=elder_id,
        activity_type=activity_type,
    )
    return activity


@transaction.atomic
def update_care_activity(
    care_activity_id: uuid.UUID,
    *,
    display_title: str | None = None,
    display_subtitle: str | None = None,
    display_icon: str | None = None,
    confirmation_requirement: dict[str, Any] | None = None,
    compartment_assignment_reference: str | None = None,
    recurrence_definition: dict[str, Any] | None = None,
    timezone_name: str | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> CareActivity:
    activity = CareActivity.objects.select_for_update().get(pk=care_activity_id)
    if activity.status in {CareActivityStatus.ENDED, CareActivityStatus.CANCELLED}:
        raise InvalidCareActivityStateError("Cannot update an ended or cancelled care activity.")

    update_fields: list[str] = []
    if display_title is not None:
        activity.display_title = display_title
        update_fields.append("display_title")
    if display_subtitle is not None:
        activity.display_subtitle = display_subtitle
        update_fields.append("display_subtitle")
    if display_icon is not None:
        activity.display_icon = display_icon
        update_fields.append("display_icon")
    if confirmation_requirement is not None:
        activity.confirmation_requirement = confirmation_requirement
        update_fields.append("confirmation_requirement")
    if compartment_assignment_reference is not None:
        activity.compartment_assignment_reference = compartment_assignment_reference
        update_fields.append("compartment_assignment_reference")

    if update_fields:
        bump_care_activity_version(activity, update_fields)
        update_fields.append("updated_at")
        activity.save(update_fields=update_fields)

    if any(value is not None for value in (recurrence_definition, timezone_name, start_at, end_at)):
        update_schedule(
            activity.schedule_definition_id,
            recurrence_definition=recurrence_definition,
            timezone_name=timezone_name,
            start_at=start_at,
            end_at=end_at,
        )
        bump_care_activity_version(activity, ["aggregate_version"])
        activity.save(update_fields=["aggregate_version", "updated_at"])

    emit_care_activity_updated(care_activity_id=activity.id, status=activity.status)
    return activity


@transaction.atomic
def pause_care_activity(*, care_activity_id: uuid.UUID) -> CareActivity:
    activity = CareActivity.objects.select_for_update().get(pk=care_activity_id)
    if activity.status != CareActivityStatus.ACTIVE:
        raise InvalidCareActivityStateError("Only active care activities can be paused.")
    activity.status = CareActivityStatus.PAUSED
    update_fields = ["status", "updated_at"]
    bump_care_activity_version(activity, update_fields)
    activity.save(update_fields=update_fields)
    pause_schedule(activity.schedule_definition_id)
    emit_care_activity_paused(care_activity_id=activity.id)
    return activity


@transaction.atomic
def resume_care_activity(*, care_activity_id: uuid.UUID) -> CareActivity:
    activity = CareActivity.objects.select_for_update().get(pk=care_activity_id)
    if activity.status != CareActivityStatus.PAUSED:
        raise InvalidCareActivityStateError("Only paused care activities can be resumed.")
    activity.status = CareActivityStatus.ACTIVE
    update_fields = ["status", "updated_at"]
    bump_care_activity_version(activity, update_fields)
    activity.save(update_fields=update_fields)
    resume_schedule(activity.schedule_definition_id)
    emit_care_activity_resumed(care_activity_id=activity.id)
    return activity


@transaction.atomic
def end_care_activity(*, care_activity_id: uuid.UUID) -> CareActivity:
    activity = CareActivity.objects.select_for_update().get(pk=care_activity_id)
    if activity.status in {CareActivityStatus.ENDED, CareActivityStatus.CANCELLED}:
        return activity
    activity.status = CareActivityStatus.ENDED
    update_fields = ["status", "updated_at"]
    bump_care_activity_version(activity, update_fields)
    activity.save(update_fields=update_fields)
    cancel_schedule(activity.schedule_definition_id)
    emit_care_activity_ended(care_activity_id=activity.id)
    return activity
