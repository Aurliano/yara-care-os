"""Integration event handlers."""

from __future__ import annotations

import uuid
from typing import Any

from domains.care.enums import WorkflowExecutionResultType
from domains.care.services.activities import get_care_activity
from domains.care.services.interpretation import interpret_execution_result
from domains.care.services.occurrence_due import handle_occurrence_due_event
from domains.care.services.prescriptions import get_prescription
from domains.care.services.sync_export import build_care_activity_sync_delta
from domains.workflow.services.evidence import submit_domain_event_evidence
from integration.context import IntegrationContext
from integration.observability import logging as integration_logging
from integration.observability.metrics import increment
from integration.runtime.action_handlers.registry import REGISTRY
from integration.runtime.adapters.synchronization import submit_care_delta_for_replica
from integration.services.hub_provisioning import get_assigned_hub_replica_identifier


def handle_occurrence_due(ctx: IntegrationContext, payload: dict[str, Any]) -> None:
    event_id = uuid.UUID(payload["event_id"])
    handle_occurrence_due_event(event_id=event_id)
    increment("integration.event.occurrence_due")


def handle_execution_started(ctx: IntegrationContext, payload: dict[str, Any]) -> None:
    execution_id = uuid.UUID(payload["workflow_execution_id"])
    ctx = ctx.with_execution(execution_id)
    REGISTRY.dispatch(ctx, payload=payload)
    increment("integration.event.execution_started")


def handle_escalation_triggered(ctx: IntegrationContext, payload: dict[str, Any]) -> None:
    execution_id = uuid.UUID(payload["workflow_execution_id"])
    ctx = ctx.with_execution(execution_id)
    REGISTRY.dispatch(ctx, payload=payload)
    increment("integration.event.escalation_triggered")


def handle_execution_confirmed(ctx: IntegrationContext, payload: dict[str, Any]) -> None:
    execution_id = uuid.UUID(payload["workflow_execution_id"])
    interpret_execution_result(
        workflow_execution_id=execution_id,
        result_type=WorkflowExecutionResultType.EXECUTION_CONFIRMED,
    )
    increment("integration.event.execution_confirmed")


def handle_execution_missed(ctx: IntegrationContext, payload: dict[str, Any]) -> None:
    execution_id = uuid.UUID(payload["workflow_execution_id"])
    interpret_execution_result(
        workflow_execution_id=execution_id,
        result_type=WorkflowExecutionResultType.EXECUTION_MISSED,
    )
    increment("integration.event.execution_missed")


def handle_device_command_completed(ctx: IntegrationContext, payload: dict[str, Any]) -> None:
    execution_reference = payload.get("execution_reference")
    if not execution_reference:
        return
    execution_id = uuid.UUID(execution_reference)
    submit_domain_event_evidence(
        execution_id=execution_id,
        evidence_type="HUB_CONFIRMATION",
        event_reference=str(payload["command_id"]),
        payload={"command_type": payload.get("command_type", "")},
    )
    increment("integration.event.device_command_completed")


def handle_communication_session_ended(ctx: IntegrationContext, payload: dict[str, Any]) -> None:
    external_ref = payload.get("external_execution_reference")
    if not external_ref or payload.get("outcome") != "ANSWERED":
        return
    execution_id = uuid.UUID(external_ref)
    submit_domain_event_evidence(
        execution_id=execution_id,
        evidence_type="COMMUNICATION_SESSION_ENDED",
        event_reference=str(payload["communication_session_id"]),
    )
    increment("integration.event.communication_session_ended")


def _submit_care_activity_delta(
    ctx: IntegrationContext,
    *,
    care_activity_id: uuid.UUID,
    idempotency_key: str,
    elder_id: uuid.UUID | None = None,
) -> None:
    replica_id = ctx.replica_id
    if replica_id is None:
        resolved_elder_id = elder_id
        if resolved_elder_id is None:
            resolved_elder_id = get_care_activity(care_activity_id).elder_id
        replica_id = get_assigned_hub_replica_identifier(elder_id=resolved_elder_id)
    if replica_id is None:
        integration_logging.log_orchestration_step(ctx, "sync_skipped_no_replica")
        return
    ctx = ctx.with_replica(replica_id)
    delta = build_care_activity_sync_delta(care_activity_id=care_activity_id)
    submit_care_delta_for_replica(
        ctx,
        delta=delta,
        idempotency_key=idempotency_key,
    )


def handle_care_activity_created(ctx: IntegrationContext, payload: dict[str, Any]) -> None:
    care_activity_id = uuid.UUID(payload["care_activity_id"])
    elder_id = uuid.UUID(payload["elder_id"]) if payload.get("elder_id") else None
    _submit_care_activity_delta(
        ctx,
        care_activity_id=care_activity_id,
        idempotency_key=f"care-created:{payload['event_id']}",
        elder_id=elder_id,
    )
    increment("integration.event.care_activity_created")


def handle_care_activity_updated(ctx: IntegrationContext, payload: dict[str, Any]) -> None:
    _submit_care_activity_delta(
        ctx,
        care_activity_id=uuid.UUID(payload["care_activity_id"]),
        idempotency_key=f"care-updated:{payload['event_id']}",
    )
    increment("integration.event.care_activity_updated")


def handle_prescription_created(ctx: IntegrationContext, payload: dict[str, Any]) -> None:
    _submit_care_activity_delta(
        ctx,
        care_activity_id=uuid.UUID(payload["care_activity_id"]),
        idempotency_key=f"prescription-created:{payload['event_id']}",
    )
    increment("integration.event.prescription_created")


def handle_prescription_updated(ctx: IntegrationContext, payload: dict[str, Any]) -> None:
    prescription = get_prescription(uuid.UUID(payload["prescription_id"]))
    _submit_care_activity_delta(
        ctx,
        care_activity_id=prescription.care_activity_id,
        idempotency_key=f"prescription-updated:{payload['event_id']}",
    )
    increment("integration.event.prescription_updated")


def handle_medication_taken(ctx: IntegrationContext, payload: dict[str, Any]) -> None:
    care_activity_id = uuid.UUID(payload["care_activity_id"])
    if ctx.replica_id is None:
        integration_logging.log_orchestration_step(ctx, "sync_skipped_no_replica")
        return
    delta = build_care_activity_sync_delta(care_activity_id=care_activity_id)
    submit_care_delta_for_replica(
        ctx,
        delta=delta,
        idempotency_key=f"care-taken:{payload['care_completion_id']}",
    )
    increment("integration.event.medication_taken")


def handle_medication_missed(ctx: IntegrationContext, payload: dict[str, Any]) -> None:
    care_activity_id = uuid.UUID(payload["care_activity_id"])
    if ctx.replica_id is None:
        return
    delta = build_care_activity_sync_delta(care_activity_id=care_activity_id)
    submit_care_delta_for_replica(
        ctx,
        delta=delta,
        idempotency_key=f"care-missed:{payload['care_completion_id']}",
    )
    increment("integration.event.medication_missed")


EVENT_HANDLERS = {
    "OccurrenceDue": handle_occurrence_due,
    "ExecutionStarted": handle_execution_started,
    "EscalationTriggered": handle_escalation_triggered,
    "ExecutionConfirmed": handle_execution_confirmed,
    "ExecutionMissed": handle_execution_missed,
    "DeviceCommandCompleted": handle_device_command_completed,
    "CommunicationSessionEnded": handle_communication_session_ended,
    "CareActivityCreated": handle_care_activity_created,
    "CareActivityUpdated": handle_care_activity_updated,
    "PrescriptionCreated": handle_prescription_created,
    "PrescriptionUpdated": handle_prescription_updated,
    "MedicationTaken": handle_medication_taken,
    "MedicationMissed": handle_medication_missed,
}
