"""NOTIFY_CAREGIVER escalation writes an in-app caregiver alert."""

import uuid
from datetime import timedelta

import pytest
from django.utils import timezone

from domains.care.services.prescriptions import create_prescription
from domains.notification.models import CaregiverAlert
from domains.scheduling.enums import OccurrenceStatus
from domains.scheduling.models import Occurrence
from domains.scheduling.services.due import process_due_occurrences
from domains.workflow.medication_reminder_policy import medication_reminder_definition
from domains.workflow.models import WorkflowExecution
from domains.workflow.services.executions import create_workflow_definition
from domains.workflow.services.timeout import process_timed_out_execution
from integration.context import IntegrationContext
from integration.runtime.dispatcher import process_pending_events


@pytest.mark.django_db
def test_notify_caregiver_writes_attention_alert(
    licensed_elder,
    recurrence_definition,
    schedule_start_at,
):
    workflow = create_workflow_definition(
        code=f"wf-notify-{uuid.uuid4().hex[:8]}",
        name="Notify Policy",
        definition=medication_reminder_definition(),
    )
    prescription = create_prescription(
        elder_id=licensed_elder.id,
        workflow_definition_id=workflow.id,
        recurrence_definition=recurrence_definition,
        timezone_name="UTC",
        start_at=schedule_start_at,
        display_title="Morning pill",
        medication_reference="med-notify",
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

    ctx = IntegrationContext.new()
    process_pending_events(ctx, limit=200)
    execution = WorkflowExecution.objects.get(occurrence_id=occurrence.id)

    for _ in range(3):
        execution.active_until = timezone.now() - timedelta(seconds=1)
        execution.save(update_fields=["active_until"])
        process_timed_out_execution(execution)
        execution.refresh_from_db()

    assert execution.current_action["type"] == "NOTIFY_CAREGIVER"
    process_pending_events(ctx, limit=200)

    alert = CaregiverAlert.objects.get(source_type="NOTIFY_CAREGIVER")
    assert alert.elder_id == licensed_elder.id
    assert alert.severity == "attention"
    assert "هنوز مصرف نشده" in alert.title
    assert "Morning pill" in alert.title
