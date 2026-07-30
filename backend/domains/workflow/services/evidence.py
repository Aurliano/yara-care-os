"""Confirmation evidence submission and evaluation."""

from __future__ import annotations

import uuid
from typing import Any

from django.db import IntegrityError, transaction
from django.utils import timezone

from domains.workflow.definition_schema import get_accepted_evidence_types, validate_workflow_definition
from domains.workflow.enums import EvidenceSourceType, ExecutionStatus
from domains.workflow.evidence_types import is_approved_evidence_type
from domains.workflow.exceptions import InvalidEvidenceError, InvalidExecutionStateError
from domains.workflow.models import ConfirmationEvidence, WorkflowExecution
from domains.workflow.services.events import emit_execution_confirmed
from domains.workflow.services.executions import _ensure_not_terminal, get_execution


@transaction.atomic
def submit_confirmation_evidence(
    *,
    execution_id: uuid.UUID,
    evidence_type: str,
    source_type: str,
    source_reference: str,
    actor_user_id: uuid.UUID | None = None,
    payload: dict[str, Any] | None = None,
) -> WorkflowExecution:
    execution = WorkflowExecution.objects.select_for_update().select_related("workflow_definition").get(
        pk=execution_id
    )

    existing_evidence = ConfirmationEvidence.objects.filter(
        workflow_execution=execution,
        source_type=source_type,
        source_reference=source_reference,
    ).first()
    if existing_evidence is not None:
        execution.refresh_from_db()
        return execution

    _ensure_not_terminal(execution)
    if execution.status != ExecutionStatus.ACTIVE:
        raise InvalidExecutionStateError("Evidence can only be submitted for active executions.")

    definition = validate_workflow_definition(execution.workflow_definition.definition)
    accepted_types = get_accepted_evidence_types(definition)
    if evidence_type not in accepted_types:
        raise InvalidEvidenceError("Evidence type is not accepted by confirmation policy.")
    if not is_approved_evidence_type(evidence_type):
        raise InvalidEvidenceError("Unsupported evidence type.")
    if source_type not in EvidenceSourceType.values:
        raise InvalidEvidenceError("Unsupported evidence source type.")

    try:
        ConfirmationEvidence.objects.create(
            workflow_execution=execution,
            evidence_type=evidence_type,
            source_type=source_type,
            source_reference=source_reference,
            actor_user_id=actor_user_id,
            payload=payload or {},
        )
    except IntegrityError:
        execution.refresh_from_db()
        return execution

    now = timezone.now()
    execution.status = ExecutionStatus.CONFIRMED
    execution.completed_at = now
    execution.save(update_fields=["status", "completed_at", "updated_at"])
    emit_execution_confirmed(execution_id=execution.id, occurred_at=now)
    return execution


@transaction.atomic
def submit_domain_event_evidence(
    *,
    execution_id: uuid.UUID,
    evidence_type: str,
    event_reference: str,
    payload: dict[str, Any] | None = None,
) -> WorkflowExecution:
    return submit_confirmation_evidence(
        execution_id=execution_id,
        evidence_type=evidence_type,
        source_type=EvidenceSourceType.DOMAIN_EVENT,
        source_reference=event_reference,
        payload=payload,
    )


@transaction.atomic
def submit_direct_interaction_evidence(
    *,
    execution_id: uuid.UUID,
    evidence_type: str,
    interaction_reference: str,
    actor_user_id: uuid.UUID | None = None,
    payload: dict[str, Any] | None = None,
) -> WorkflowExecution:
    return submit_confirmation_evidence(
        execution_id=execution_id,
        evidence_type=evidence_type,
        source_type=EvidenceSourceType.DIRECT_INTERACTION,
        source_reference=interaction_reference,
        actor_user_id=actor_user_id,
        payload=payload,
    )
