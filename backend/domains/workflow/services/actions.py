"""Retry, escalation, and action result handling."""

from __future__ import annotations

import uuid
from typing import Any

from django.db import IntegrityError, transaction
from django.utils import timezone

from domains.workflow.definition_schema import (
    get_escalation_steps,
    get_retry_policy,
    get_step_timeout_seconds,
    validate_workflow_definition,
)
from domains.workflow.enums import ActionResultStatus, ExecutionStatus
from domains.workflow.exceptions import EscalationNotAllowedError, InvalidExecutionStateError, RetryNotAllowedError
from domains.workflow.models import ActionResult, WorkflowExecution
from domains.workflow.services.events import emit_escalation_triggered
from domains.workflow.services.executions import _ensure_not_terminal, _set_active_action, get_execution


@transaction.atomic
def report_action_result(
    *,
    execution_id: uuid.UUID,
    action_reference: str,
    action_type: str,
    result_status: str,
    payload: dict[str, Any] | None = None,
) -> ActionResult:
    execution = get_execution(execution_id)
    _ensure_not_terminal(execution)
    if result_status not in ActionResultStatus.values:
        raise InvalidExecutionStateError("Invalid action result status.")

    existing = ActionResult.objects.filter(
        workflow_execution=execution,
        action_reference=action_reference,
    ).first()
    if existing is not None:
        return existing

    try:
        return ActionResult.objects.create(
            workflow_execution=execution,
            action_reference=action_reference,
            action_type=action_type,
            result_status=result_status,
            payload=payload or {},
        )
    except IntegrityError:
        return ActionResult.objects.get(
            workflow_execution=execution,
            action_reference=action_reference,
        )


@transaction.atomic
def advance_escalation(*, execution_id: uuid.UUID) -> WorkflowExecution:
    execution = WorkflowExecution.objects.select_for_update().select_related("workflow_definition").get(
        pk=execution_id
    )
    _ensure_not_terminal(execution)
    if execution.status != ExecutionStatus.ACTIVE:
        raise InvalidExecutionStateError("Only active executions can escalate.")

    return _advance_escalation_step(execution)


def _advance_escalation_step(execution: WorkflowExecution) -> WorkflowExecution:
    definition = validate_workflow_definition(execution.workflow_definition.definition)
    steps = get_escalation_steps(definition)
    next_index = execution.escalation_index + 1
    if next_index > len(steps):
        raise EscalationNotAllowedError("No further escalation steps are defined.")

    step = steps[next_index - 1]
    action = step["action"]
    timeout_seconds = int(step.get("timeout_seconds", get_step_timeout_seconds(definition)))

    execution.escalation_index = next_index
    execution.save(update_fields=["escalation_index", "updated_at"])
    _set_active_action(
        execution,
        action=action,
        step_name=f"escalation_{next_index}",
        timeout_seconds=timeout_seconds,
    )
    emit_escalation_triggered(
        execution_id=execution.id,
        escalation_index=next_index,
        action_type=action["type"],
    )
    return execution


@transaction.atomic
def apply_retry_for_timeout(execution: WorkflowExecution) -> WorkflowExecution:
    definition = validate_workflow_definition(execution.workflow_definition.definition)
    retry_policy = get_retry_policy(definition)
    if retry_policy is None:
        raise RetryNotAllowedError("Retry is not configured.")

    max_retries = int(retry_policy.get("max_retries", 0))
    if execution.retry_count >= max_retries:
        raise RetryNotAllowedError("Maximum retry count reached.")

    action = retry_policy.get("action", execution.current_action)
    timeout_seconds = int(retry_policy.get("timeout_seconds", get_step_timeout_seconds(definition)))

    execution.retry_count += 1
    execution.save(update_fields=["retry_count", "updated_at"])
    _set_active_action(
        execution,
        action=action,
        step_name=f"retry_{execution.retry_count}",
        timeout_seconds=timeout_seconds,
    )
    return execution
