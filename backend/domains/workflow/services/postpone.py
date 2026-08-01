"""Postpone execution according to workflow policy."""

from __future__ import annotations

import uuid
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from domains.workflow.definition_schema import get_postpone_policy, validate_workflow_definition
from domains.workflow.enums import ExecutionStatus
from domains.workflow.exceptions import InvalidExecutionStateError, PostponeNotAllowedError
from domains.workflow.models import WorkflowExecution
from domains.workflow.services.executions import _ensure_not_terminal
from domains.workflow.services.events import emit_execution_postponed
from domains.workflow.versioning import bump_workflow_execution_version


@transaction.atomic
def postpone_execution(*, execution_id: uuid.UUID) -> WorkflowExecution:
    execution = WorkflowExecution.objects.select_for_update().select_related("workflow_definition").get(
        pk=execution_id
    )
    _ensure_not_terminal(execution)
    if execution.status != ExecutionStatus.ACTIVE:
        raise InvalidExecutionStateError("Only active executions can be postponed.")

    definition = validate_workflow_definition(execution.workflow_definition.definition)
    policy = get_postpone_policy(definition)
    if policy is None or not policy.get("allowed", False):
        raise PostponeNotAllowedError("Postpone is not allowed by workflow policy.")

    max_count = int(policy.get("max_count", 0))
    if execution.postpone_count >= max_count:
        raise PostponeNotAllowedError("Maximum postpone count reached.")

    delay_seconds = int(policy.get("delay_seconds", 0))
    if delay_seconds <= 0:
        raise PostponeNotAllowedError("Postpone delay is not configured.")

    now = timezone.now()
    execution.postpone_count += 1
    execution.active_until = now + timedelta(seconds=delay_seconds)
    update_fields = ["postpone_count", "active_until", "updated_at"]
    bump_workflow_execution_version(execution, update_fields)
    execution.save(update_fields=update_fields)
    emit_execution_postponed(execution_id=execution.id, postpone_count=execution.postpone_count)
    return execution
