"""Hub confirmation adapter."""

from __future__ import annotations

import uuid

from django.utils import timezone

from domains.care.services.activities import get_care_activity_for_schedule
from domains.scheduling.services.due import mark_occurrence_due
from domains.scheduling.services.occurrences import get_occurrence
from domains.workflow.exceptions import ExecutionNotFoundError
from domains.workflow.identity import compute_execution_id
from domains.workflow.services.evidence import submit_direct_interaction_evidence
from domains.workflow.services.executions import get_execution, start_execution
from integration.context import IntegrationContext
from integration.observability import logging as integration_logging


def submit_hub_confirmation(
    ctx: IntegrationContext,
    *,
    execution_id: uuid.UUID,
    interaction_reference: str,
    evidence_type: str = "HUB_CONFIRMATION",
    actor_user_id: uuid.UUID | None = None,
    occurrence_id: uuid.UUID | None = None,
) -> dict[str, str]:
    ctx = ctx.with_execution(execution_id)
    if occurrence_id is not None:
        _reconcile_missing_execution(ctx, execution_id=execution_id, occurrence_id=occurrence_id)
    execution = submit_direct_interaction_evidence(
        execution_id=execution_id,
        evidence_type=evidence_type,
        interaction_reference=interaction_reference,
        actor_user_id=actor_user_id or ctx.actor_id,
    )
    integration_logging.log_orchestration_step(ctx, "hub_confirmation_submitted")
    return {"workflow_execution_id": str(execution.id), "status": execution.status}


def _reconcile_missing_execution(
    ctx: IntegrationContext,
    *,
    execution_id: uuid.UUID,
    occurrence_id: uuid.UUID,
) -> None:
    """Start the execution the offline Hub already ran locally.

    The Hub bootstraps an execution for a due occurrence while offline
    (ADR-012 Decision 1) using the same deterministic id the cloud would use.
    Without this, an elder confirmation is rejected forever whenever the cloud
    integration cycle has not reached that occurrence yet.
    """
    if compute_execution_id(occurrence_id=occurrence_id) != execution_id:
        integration_logging.log_orchestration_step(ctx, "hub_confirmation_execution_id_mismatch")
        return
    try:
        get_execution(execution_id)
        return
    except ExecutionNotFoundError:
        pass

    occurrence = get_occurrence(occurrence_id)
    if occurrence.scheduled_for > timezone.now():
        # A Hub clock running ahead must not pull a future dose forward; the
        # upload retries once this occurrence is genuinely due.
        integration_logging.log_orchestration_step(ctx, "hub_confirmation_occurrence_not_due_yet")
        return

    mark_occurrence_due(occurrence)
    activity = get_care_activity_for_schedule(occurrence.schedule_definition_id)
    start_execution(
        occurrence_id=occurrence_id,
        workflow_definition_id=activity.workflow_definition_id,
        dispatch_context={
            "elder_id": str(activity.elder_id),
            "care_activity_id": str(activity.id),
            "activity_type": activity.activity_type,
            "schedule_definition_id": str(occurrence.schedule_definition_id),
        },
    )
    integration_logging.log_orchestration_step(ctx, "hub_confirmation_execution_reconciled")
