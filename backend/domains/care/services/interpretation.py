"""Care interpretation of Workflow execution results."""

from __future__ import annotations

import uuid
from datetime import datetime

from django.db import IntegrityError, transaction
from django.utils import timezone

from domains.care.enums import (
    CareActivityType,
    CompletionState,
    WorkflowExecutionResultType,
)
from domains.care.exceptions import CareActivityNotFoundError, InvalidExecutionResultError
from domains.care.identity import compute_care_completion_id
from domains.care.models import CareActivity, CareCompletion, Prescription
from domains.care.services.activities import get_care_activity_for_schedule
from domains.care.services.events import (
    emit_care_activity_completed,
    emit_medication_missed,
    emit_medication_taken,
)
from domains.workflow.services.executions import get_execution


def get_care_completion_history(*, care_activity_id: uuid.UUID) -> list[CareCompletion]:
    return list(
        CareCompletion.objects.filter(care_activity_id=care_activity_id).order_by("-interpreted_at")
    )


def _resolve_completion_state(
    *,
    activity: CareActivity,
    result_type: str,
    is_prescription: bool,
) -> CompletionState:
    if result_type == WorkflowExecutionResultType.EXECUTION_CONFIRMED:
        if is_prescription:
            return CompletionState.MEDICATION_TAKEN
        return CompletionState.CARE_ACTIVITY_COMPLETED
    if result_type == WorkflowExecutionResultType.EXECUTION_MISSED:
        if is_prescription:
            return CompletionState.MEDICATION_MISSED
        return CompletionState.CARE_ACTIVITY_MISSED
    if result_type == WorkflowExecutionResultType.EXECUTION_CANCELLED:
        return CompletionState.CARE_ACTIVITY_CANCELLED
    if result_type == WorkflowExecutionResultType.EXECUTION_FAILED:
        return CompletionState.CARE_ACTIVITY_FAILED
    raise InvalidExecutionResultError("Unsupported execution result type.")


def _emit_completion_event(
    *,
    activity: CareActivity,
    completion: CareCompletion,
    completion_state: CompletionState,
) -> None:
    if completion_state == CompletionState.MEDICATION_TAKEN:
        emit_medication_taken(
            care_activity_id=activity.id,
            care_completion_id=completion.id,
            workflow_execution_id=completion.workflow_execution_id,
        )
        return
    if completion_state == CompletionState.MEDICATION_MISSED:
        emit_medication_missed(
            care_activity_id=activity.id,
            care_completion_id=completion.id,
            workflow_execution_id=completion.workflow_execution_id,
        )
        return
    if completion_state == CompletionState.CARE_ACTIVITY_COMPLETED:
        emit_care_activity_completed(
            care_activity_id=activity.id,
            care_completion_id=completion.id,
            workflow_execution_id=completion.workflow_execution_id,
        )


@transaction.atomic
def interpret_execution_result(
    *,
    workflow_execution_id: uuid.UUID,
    result_type: str,
    occurred_at: datetime | None = None,
) -> CareCompletion:
    if result_type not in WorkflowExecutionResultType.values:
        raise InvalidExecutionResultError("Unsupported execution result type.")

    existing = CareCompletion.objects.filter(workflow_execution_id=workflow_execution_id).first()
    if existing is not None:
        return existing

    execution = get_execution(workflow_execution_id)
    occurrence = execution.occurrence
    try:
        activity = get_care_activity_for_schedule(occurrence.schedule_definition_id)
    except CareActivityNotFoundError as exc:
        raise InvalidExecutionResultError(
            "No care activity is linked to the execution occurrence schedule."
        ) from exc

    is_prescription = activity.activity_type == CareActivityType.MEDICATION and Prescription.objects.filter(
        pk=activity.id
    ).exists()
    completion_state = _resolve_completion_state(
        activity=activity,
        result_type=result_type,
        is_prescription=is_prescription,
    )
    interpreted_at = occurred_at or timezone.now()
    completion_id = compute_care_completion_id(workflow_execution_id=workflow_execution_id)

    try:
        completion = CareCompletion.objects.create(
            id=completion_id,
            care_activity=activity,
            occurrence_id=occurrence.id,
            workflow_execution_id=workflow_execution_id,
            completion_state=completion_state,
            interpreted_at=interpreted_at,
        )
    except IntegrityError:
        return CareCompletion.objects.get(workflow_execution_id=workflow_execution_id)

    _emit_completion_event(
        activity=activity,
        completion=completion,
        completion_state=completion_state,
    )
    return completion
