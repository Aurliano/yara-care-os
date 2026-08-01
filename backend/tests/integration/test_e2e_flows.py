"""End-to-end integration runtime tests."""

import uuid
from datetime import datetime, timedelta

import pytest
from django.utils import timezone
from zoneinfo import ZoneInfo

from domains.care.services.prescriptions import create_prescription
from domains.device.enums import AssignmentType
from domains.device.services.assignments import assign_device
from domains.device.services.commands import get_commands
from domains.event.models import EventRecord
from domains.scheduling.enums import OccurrenceStatus
from domains.scheduling.models import Occurrence
from domains.scheduling.services.due import process_due_occurrences
from domains.synchronization.models import SynchronizationOperation
from domains.workflow.enums import ExecutionStatus
from domains.workflow.services.executions import create_workflow_definition
from integration.context import IntegrationContext
from integration.runtime.adapters.confirmations import submit_hub_confirmation
from integration.runtime.adapters.device import complete_hub_command, deliver_hub_command
from integration.runtime.dispatcher import process_pending_events
from integration.runtime.scheduler import run_integration_cycle, run_workflow_timeout_scan


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt


@pytest.mark.django_db
def test_reminder_completed_end_to_end(
    licensed_elder,
    hub_device,
    workflow_definition,
    recurrence_definition,
    schedule_start_at,
):
    assign_device(
        device_id=hub_device.id,
        elder_id=licensed_elder.id,
        assignment_type=AssignmentType.OWNED,
    )
    prescription = create_prescription(
        elder_id=licensed_elder.id,
        workflow_definition_id=workflow_definition.id,
        recurrence_definition=recurrence_definition,
        timezone_name="UTC",
        start_at=schedule_start_at,
        display_title="Morning pill",
        medication_reference="med-1",
        dosage_information="1 tablet",
        elder_friendly_description="Take pill",
    )
    occurrence = Occurrence.objects.filter(
        schedule_definition_id=prescription.care_activity.schedule_definition_id
    ).first()
    occurrence.status = OccurrenceStatus.SCHEDULED
    occurrence.scheduled_for = timezone.now() - timedelta(minutes=1)
    occurrence.save(update_fields=["status", "scheduled_for"])
    process_due_occurrences(now=timezone.now())

    replica_id = uuid.uuid4()
    ctx = IntegrationContext.new().with_replica(replica_id)
    run_integration_cycle(ctx)

    commands = get_commands(device_id=hub_device.id)
    assert commands
    command = commands[0]
    deliver_hub_command(ctx, command_id=command.id)
    complete_hub_command(ctx, command_id=command.id, result={"confirmed": True})

    process_pending_events(ctx, limit=500)

    assert EventRecord.objects.filter(event_type="MedicationTaken").exists()
    assert SynchronizationOperation.objects.filter(operation_type="DELTA").exists()


@pytest.mark.django_db
def test_reminder_missed_end_to_end(
    licensed_elder,
    hub_device,
    recurrence_definition,
    schedule_start_at,
):
    missed_workflow = create_workflow_definition(
        code=f"wf-miss-{uuid.uuid4().hex[:8]}",
        name="Immediate Miss Workflow",
        definition={
            "initial_action": {"type": "SHOW_REMINDER"},
            "confirmation_policy": {"accepted_evidence_types": ["HUB_CONFIRMATION"]},
            "step_timeout_seconds": 60,
        },
    )
    assign_device(device_id=hub_device.id, elder_id=licensed_elder.id, assignment_type=AssignmentType.OWNED)
    prescription = create_prescription(
        elder_id=licensed_elder.id,
        workflow_definition_id=missed_workflow.id,
        recurrence_definition=recurrence_definition,
        timezone_name="UTC",
        start_at=schedule_start_at,
        display_title="Missed pill",
        medication_reference="med-2",
        dosage_information="1 tablet",
        elder_friendly_description="Missed pill",
    )
    occurrence = Occurrence.objects.filter(
        schedule_definition_id=prescription.care_activity.schedule_definition_id
    ).first()
    occurrence.status = OccurrenceStatus.SCHEDULED
    occurrence.scheduled_for = timezone.now() - timedelta(minutes=1)
    occurrence.save(update_fields=["status", "scheduled_for"])
    process_due_occurrences(now=timezone.now())

    ctx = IntegrationContext.new().with_replica(uuid.uuid4())
    run_integration_cycle(ctx)

    from domains.workflow.models import WorkflowExecution

    execution = WorkflowExecution.objects.get()
    execution.active_until = timezone.now() - timedelta(seconds=1)
    execution.save(update_fields=["active_until"])
    run_workflow_timeout_scan(ctx)
    process_pending_events(ctx, limit=500)

    assert EventRecord.objects.filter(event_type="MedicationMissed").exists()


@pytest.mark.django_db
def test_hub_confirmation_idempotent(
    licensed_elder,
    workflow_definition,
    due_occurrence,
):
    from domains.workflow.services.executions import start_execution

    execution = start_execution(
        occurrence_id=due_occurrence.id,
        workflow_definition_id=workflow_definition.id,
    )
    ctx = IntegrationContext.new()
    submit_hub_confirmation(
        ctx,
        execution_id=execution.id,
        interaction_reference="hub-dup-1",
    )
    submit_hub_confirmation(
        ctx,
        execution_id=execution.id,
        interaction_reference="hub-dup-1",
    )
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.CONFIRMED


@pytest.mark.django_db
def test_correlation_id_propagation_in_context():
    correlation = "corr-test-123"
    ctx = IntegrationContext.new(correlation_id=correlation)
    assert ctx.correlation_id == correlation
    ctx2 = ctx.with_execution(uuid.uuid4())
    assert ctx2.correlation_id == correlation
