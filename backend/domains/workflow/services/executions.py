"""Workflow execution lifecycle services."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

from django.db import IntegrityError, transaction
from django.utils import timezone

from domains.scheduling.enums import OccurrenceStatus
from domains.scheduling.services.occurrences import get_occurrence
from domains.workflow.definition_schema import (
    get_initial_action,
    get_step_timeout_seconds,
    validate_workflow_definition,
)
from domains.workflow.enums import TERMINAL_EXECUTION_STATUSES, ExecutionStatus
from domains.workflow.exceptions import (
    ExecutionNotFoundError,
    InvalidExecutionStateError,
    WorkflowDefinitionConflictError,
    WorkflowNotFoundError,
)
from domains.workflow.identity import compute_execution_id
from domains.workflow.models import WorkflowDefinition, WorkflowExecution
from domains.workflow.services.events import emit_execution_started


def get_workflow_definition(workflow_definition_id: uuid.UUID) -> WorkflowDefinition:
    try:
        return WorkflowDefinition.objects.get(pk=workflow_definition_id)
    except WorkflowDefinition.DoesNotExist as exc:
        raise WorkflowNotFoundError("Workflow definition not found.") from exc


def get_workflow_definition_by_code(code: str) -> WorkflowDefinition:
    try:
        return WorkflowDefinition.objects.get(code=code)
    except WorkflowDefinition.DoesNotExist as exc:
        raise WorkflowNotFoundError("Workflow definition not found.") from exc


def get_execution(execution_id: uuid.UUID) -> WorkflowExecution:
    try:
        return WorkflowExecution.objects.select_related(
            "workflow_definition",
            "occurrence",
        ).get(pk=execution_id)
    except WorkflowExecution.DoesNotExist as exc:
        raise ExecutionNotFoundError("Workflow execution not found.") from exc


def get_execution_status(execution_id: uuid.UUID) -> str:
    return get_execution(execution_id).status


def get_active_executions() -> list[WorkflowExecution]:
    return list(
        WorkflowExecution.objects.filter(status=ExecutionStatus.ACTIVE).order_by("-started_at")
    )


def _ensure_not_terminal(execution: WorkflowExecution) -> None:
    if execution.status in TERMINAL_EXECUTION_STATUSES:
        raise InvalidExecutionStateError("Terminal executions cannot be modified.")


def _ensure_matching_workflow_definition(
    execution: WorkflowExecution,
    workflow_definition_id: uuid.UUID,
) -> None:
    if execution.workflow_definition_id != workflow_definition_id:
        raise WorkflowDefinitionConflictError(
            "An execution already exists for this occurrence with a different workflow definition."
        )


def _set_active_action(
    execution: WorkflowExecution,
    *,
    action: dict[str, Any],
    step_name: str,
    timeout_seconds: int,
    now: datetime | None = None,
) -> None:
    now = now or timezone.now()
    execution.status = ExecutionStatus.ACTIVE
    execution.current_action = action
    execution.current_step = step_name
    execution.active_until = now + timedelta(seconds=timeout_seconds)
    execution.started_at = execution.started_at or now
    execution.completed_at = None
    execution.save(
        update_fields=[
            "status",
            "current_action",
            "current_step",
            "active_until",
            "started_at",
            "completed_at",
            "updated_at",
        ]
    )


@transaction.atomic
def start_execution(
    *,
    occurrence_id: uuid.UUID,
    workflow_definition_id: uuid.UUID,
) -> WorkflowExecution:
    """Start or return the WorkflowExecution for an Occurrence.

    Caller must supply workflow_definition_id explicitly until Care owns
    schedule/workflow association in B6.
    """
    occurrence = get_occurrence(occurrence_id)
    if occurrence.status != OccurrenceStatus.DUE:
        raise InvalidExecutionStateError("Execution can only start for DUE occurrences.")

    workflow_definition = get_workflow_definition(workflow_definition_id)
    validate_workflow_definition(workflow_definition.definition)

    execution_id = compute_execution_id(occurrence_id=occurrence_id)
    existing = WorkflowExecution.objects.select_for_update().filter(pk=execution_id).first()
    if existing is not None:
        _ensure_matching_workflow_definition(existing, workflow_definition_id)
        if existing.status in TERMINAL_EXECUTION_STATUSES:
            return existing
        if existing.status == ExecutionStatus.ACTIVE:
            return existing
        if existing.status == ExecutionStatus.PENDING:
            _activate_pending_execution(existing, workflow_definition)
            return existing
        return existing

    try:
        execution = WorkflowExecution.objects.create(
            id=execution_id,
            occurrence=occurrence,
            workflow_definition=workflow_definition,
            status=ExecutionStatus.PENDING,
        )
    except IntegrityError:
        execution = WorkflowExecution.objects.select_for_update().get(pk=execution_id)
        _ensure_matching_workflow_definition(execution, workflow_definition_id)
        if execution.status in TERMINAL_EXECUTION_STATUSES or execution.status == ExecutionStatus.ACTIVE:
            return execution

    _activate_pending_execution(execution, workflow_definition)
    return execution


def _activate_pending_execution(execution: WorkflowExecution, workflow_definition: WorkflowDefinition) -> None:
    definition = validate_workflow_definition(workflow_definition.definition)
    initial_action = get_initial_action(definition)
    timeout_seconds = get_step_timeout_seconds(definition)
    _set_active_action(
        execution,
        action=initial_action,
        step_name="initial",
        timeout_seconds=timeout_seconds,
    )
    emit_execution_started(
        execution_id=execution.id,
        occurrence_id=execution.occurrence_id,
        workflow_definition_id=workflow_definition.id,
    )


@transaction.atomic
def cancel_execution(*, execution_id: uuid.UUID) -> WorkflowExecution:
    execution = WorkflowExecution.objects.select_for_update().get(pk=execution_id)
    _ensure_not_terminal(execution)
    if execution.status != ExecutionStatus.ACTIVE:
        raise InvalidExecutionStateError("Only active executions can be cancelled.")

    now = timezone.now()
    execution.status = ExecutionStatus.CANCELLED
    execution.completed_at = now
    execution.save(update_fields=["status", "completed_at", "updated_at"])

    from domains.workflow.services.events import emit_execution_cancelled

    emit_execution_cancelled(execution_id=execution.id)
    return execution


def create_workflow_definition(
    *,
    code: str,
    name: str,
    definition: dict[str, Any],
) -> WorkflowDefinition:
    validate_workflow_definition(definition)
    return WorkflowDefinition.objects.create(
        code=code,
        name=name,
        definition=definition,
    )
