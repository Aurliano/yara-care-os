"""Workflow timeout and missed execution processing."""

from __future__ import annotations

from datetime import datetime

from django.db import transaction
from django.utils import timezone

from domains.workflow.definition_schema import get_escalation_steps, get_retry_policy, validate_workflow_definition
from domains.workflow.enums import ExecutionStatus
from domains.workflow.exceptions import EscalationNotAllowedError, RetryNotAllowedError
from domains.workflow.models import WorkflowExecution
from domains.workflow.services.actions import _advance_escalation_step, apply_retry_for_timeout
from domains.workflow.services.events import emit_execution_missed
from domains.workflow.versioning import bump_workflow_execution_version


@transaction.atomic
def mark_execution_missed(execution: WorkflowExecution, *, occurred_at: datetime | None = None) -> WorkflowExecution:
    execution = WorkflowExecution.objects.select_for_update().get(pk=execution.pk)
    if execution.status != ExecutionStatus.ACTIVE:
        return execution

    occurred_at = occurred_at or timezone.now()
    execution.status = ExecutionStatus.MISSED
    execution.completed_at = occurred_at
    update_fields = ["status", "completed_at", "updated_at"]
    bump_workflow_execution_version(execution, update_fields)
    execution.save(update_fields=update_fields)
    emit_execution_missed(execution_id=execution.id, occurred_at=occurred_at)
    return execution


@transaction.atomic
def process_timed_out_execution(execution: WorkflowExecution, *, now: datetime | None = None) -> WorkflowExecution:
    execution = WorkflowExecution.objects.select_for_update().select_related("workflow_definition").get(
        pk=execution.pk
    )
    now = now or timezone.now()
    if execution.status != ExecutionStatus.ACTIVE:
        return execution
    if execution.active_until is None or execution.active_until > now:
        return execution

    definition = validate_workflow_definition(execution.workflow_definition.definition)
    retry_policy = get_retry_policy(definition)
    if retry_policy is not None:
        max_retries = int(retry_policy.get("max_retries", 0))
        if execution.retry_count < max_retries:
            try:
                return apply_retry_for_timeout(execution)
            except RetryNotAllowedError:
                pass

    steps = get_escalation_steps(definition)
    if execution.escalation_index < len(steps):
        try:
            return _advance_escalation_step(execution)
        except EscalationNotAllowedError:
            pass

    return mark_execution_missed(execution, occurred_at=now)


def process_workflow_timeouts(*, now: datetime | None = None) -> int:
    now = now or timezone.now()
    processed = 0
    timed_out = (
        WorkflowExecution.objects.filter(
            status=ExecutionStatus.ACTIVE,
            active_until__lte=now,
        )
        .select_related("workflow_definition")
        .iterator()
    )
    for execution in timed_out:
        before_status = execution.status
        process_timed_out_execution(execution, now=now)
        execution.refresh_from_db()
        if before_status == ExecutionStatus.ACTIVE and execution.status != ExecutionStatus.ACTIVE:
            processed += 1
        elif before_status == ExecutionStatus.ACTIVE and execution.active_until and execution.active_until > now:
            processed += 1
    return processed
