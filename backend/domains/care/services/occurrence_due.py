"""OccurrenceDue orchestration — Care resolves activity and starts Workflow execution."""

from __future__ import annotations

import uuid

from domains.care.enums import CareActivityStatus
from domains.care.exceptions import CareActivityNotFoundError, InvalidCareActivityStateError
from domains.care.services.activities import get_care_activity_for_schedule
from domains.event.models import EventRecord
from domains.workflow.models import WorkflowExecution
from domains.workflow.services.executions import start_execution


def handle_occurrence_due_event(*, event_id: uuid.UUID) -> WorkflowExecution:
    """Resolve CareActivity for an OccurrenceDue event and start Workflow execution."""
    event = EventRecord.objects.get(pk=event_id)
    if event.event_type != "OccurrenceDue":
        raise InvalidCareActivityStateError("Event is not an OccurrenceDue event.")

    schedule_definition_id = uuid.UUID(event.payload["schedule_definition_id"])
    occurrence_id = uuid.UUID(event.payload["occurrence_id"])

    try:
        activity = get_care_activity_for_schedule(schedule_definition_id)
    except CareActivityNotFoundError as exc:
        raise InvalidCareActivityStateError(
            "No active care activity is linked to this schedule."
        ) from exc

    if activity.status != CareActivityStatus.ACTIVE:
        raise InvalidCareActivityStateError("Care activity is not active.")

    return start_execution(
        occurrence_id=occurrence_id,
        workflow_definition_id=activity.workflow_definition_id,
        dispatch_context={
            "elder_id": str(activity.elder_id),
            "care_activity_id": str(activity.id),
            "activity_type": activity.activity_type,
            "schedule_definition_id": str(schedule_definition_id),
        },
    )
