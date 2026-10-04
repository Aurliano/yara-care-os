"""Authorization resolvers for cross-domain scheduling and workflow execution access."""

from __future__ import annotations

import uuid
from typing import Any

from domains.care.models import CareActivity
from domains.identity_access.services.authorization import user_is_associated_with_elder
from domains.scheduling.hooks import register_occurrence_access_hook, register_schedule_access_hook
from domains.workflow.hooks import register_execution_access_hook


def get_elder_for_schedule(schedule: Any) -> Any | None:
    if schedule is None:
        return None
    if hasattr(schedule, "care_activity") and schedule.care_activity is not None:
        return schedule.care_activity.elder

    activity = CareActivity.objects.filter(schedule_definition_id=schedule.id).select_related("elder").first()
    if activity is not None:
        return activity.elder

    owner_ref = getattr(schedule, "owner_reference", "")
    if owner_ref:
        if owner_ref.startswith("care_activity:"):
            ref_id = owner_ref.split(":", 1)[1]
            try:
                activity = CareActivity.objects.filter(id=uuid.UUID(ref_id)).select_related("elder").first()
                if activity is not None:
                    return activity.elder
            except (ValueError, TypeError):
                pass
        elif owner_ref.startswith("prescription:"):
            ref_id = owner_ref.split(":", 1)[1]
            try:
                activity = (
                    CareActivity.objects.filter(prescription__pk=uuid.UUID(ref_id))
                    .select_related("elder")
                    .first()
                )
                if activity is not None:
                    return activity.elder
            except (ValueError, TypeError):
                pass

    return None


def care_schedule_access_hook(user: Any, schedule: Any) -> bool:
    elder = get_elder_for_schedule(schedule)
    if elder is None:
        return False
    return user_is_associated_with_elder(user, elder)


def care_occurrence_access_hook(user: Any, occurrence: Any) -> bool:
    if occurrence is None:
        return False
    schedule = getattr(occurrence, "schedule_definition", None)
    if schedule is None and hasattr(occurrence, "schedule_definition_id"):
        from domains.scheduling.models import ScheduleDefinition

        schedule = ScheduleDefinition.objects.filter(id=occurrence.schedule_definition_id).first()
    if schedule is None:
        return False
    return care_schedule_access_hook(user, schedule)


def care_execution_access_hook(user: Any, execution: Any) -> bool:
    if execution is None:
        return False
    occurrence = getattr(execution, "occurrence", None)
    if occurrence is None and hasattr(execution, "occurrence_id"):
        from domains.scheduling.models import Occurrence

        occurrence = Occurrence.objects.filter(id=execution.occurrence_id).first()
    if occurrence is None:
        return False
    return care_occurrence_access_hook(user, occurrence)


def register_care_authorizers() -> None:
    register_schedule_access_hook(care_schedule_access_hook)
    register_occurrence_access_hook(care_occurrence_access_hook)
    register_execution_access_hook(care_execution_access_hook)
