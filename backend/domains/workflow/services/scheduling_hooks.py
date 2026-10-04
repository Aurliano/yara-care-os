"""Scheduling lifecycle hooks handled by the Workflow domain."""

from __future__ import annotations

import uuid

from domains.scheduling.exceptions import InvalidOccurrenceStateError, InvalidScheduleStateError
from domains.scheduling.hooks import (
    register_post_reschedule_hook,
    register_post_skip_hook,
    register_pre_reschedule_hook,
    register_pre_skip_hook,
)
from domains.workflow.enums import ExecutionStatus
from domains.workflow.models import WorkflowExecution


def check_skip_allowed(occurrence_id: uuid.UUID) -> None:
    if WorkflowExecution.objects.filter(
        occurrence_id=occurrence_id,
        status__in=[ExecutionStatus.CONFIRMED, ExecutionStatus.MISSED],
    ).exists():
        raise InvalidOccurrenceStateError("Occurrence already has a completed execution.")


def cancel_active_executions_for_occurrence(occurrence_id: uuid.UUID) -> None:
    try:
        from domains.workflow.services.executions import cancel_execution

        active_executions = WorkflowExecution.objects.filter(
            occurrence_id=occurrence_id,
            status__in=[ExecutionStatus.ACTIVE, ExecutionStatus.PENDING],
        )
        for execution in active_executions:
            cancel_execution(execution_id=execution.id)
    except Exception:
        pass


def check_reschedule_allowed(occurrence_id: uuid.UUID) -> None:
    if WorkflowExecution.objects.filter(
        occurrence_id=occurrence_id,
        status__in=[ExecutionStatus.CONFIRMED, ExecutionStatus.MISSED],
    ).exists():
        raise InvalidScheduleStateError(
            "Cannot reschedule an occurrence that already has a completed execution."
        )


def register_workflow_scheduling_hooks() -> None:
    register_pre_skip_hook(check_skip_allowed)
    register_post_skip_hook(cancel_active_executions_for_occurrence)
    register_pre_reschedule_hook(check_reschedule_allowed)
    register_post_reschedule_hook(cancel_active_executions_for_occurrence)
