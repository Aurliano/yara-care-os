from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from domains.care.enums import CareActivityStatus, CareActivityType, CompletionState, WorkflowExecutionResultType
from domains.care.exceptions import InvalidCareActivityStateError
from domains.care.models import CareCompletion, Prescription
from domains.care.services.activities import (
    create_care_activity,
    get_care_activity,
    pause_care_activity,
    resume_care_activity,
    end_care_activity,
    update_care_activity,
)
from domains.care.services.interpretation import get_care_completion_history, interpret_execution_result
from domains.care.services.occurrence_due import handle_occurrence_due_event
from domains.care.services.prescriptions import create_prescription, get_active_prescriptions
from domains.event.models import EventRecord
from domains.scheduling.enums import OccurrenceStatus, ScheduleStatus
from domains.scheduling.models import Occurrence, ScheduleDefinition
from domains.scheduling.services.due import mark_occurrence_due, process_due_occurrences
from domains.workflow.enums import ExecutionStatus
from domains.workflow.models import WorkflowExecution
from domains.workflow.services.evidence import submit_direct_interaction_evidence
from domains.workflow.services.executions import start_execution


@pytest.mark.django_db
def test_create_care_activity_links_schedule_and_workflow(
    elder,
    workflow_definition,
    recurrence_definition,
    schedule_start_at,
):
    activity = create_care_activity(
        elder_id=elder.id,
        activity_type=CareActivityType.GENERAL,
        workflow_definition_id=workflow_definition.id,
        recurrence_definition=recurrence_definition,
        timezone_name="UTC",
        start_at=schedule_start_at,
        display_title="Morning walk",
        confirmation_requirement={"required_evidence_types": ["HUB_CONFIRMATION"]},
    )
    assert activity.status == CareActivityStatus.ACTIVE
    assert activity.schedule_definition_id is not None
    assert activity.workflow_definition_id == workflow_definition.id
    assert ScheduleDefinition.objects.filter(pk=activity.schedule_definition_id).exists()
    assert EventRecord.objects.filter(event_type="CareActivityCreated").count() == 1


@pytest.mark.django_db
def test_care_activity_lifecycle(elder, workflow_definition, recurrence_definition, schedule_start_at):
    activity = create_care_activity(
        elder_id=elder.id,
        activity_type=CareActivityType.GENERAL,
        workflow_definition_id=workflow_definition.id,
        recurrence_definition=recurrence_definition,
        timezone_name="UTC",
        start_at=schedule_start_at,
        display_title="Check-in",
    )
    paused = pause_care_activity(care_activity_id=activity.id)
    assert paused.status == CareActivityStatus.PAUSED
    assert ScheduleDefinition.objects.get(pk=activity.schedule_definition_id).status == ScheduleStatus.PAUSED
    assert EventRecord.objects.filter(event_type="CareActivityPaused").count() == 1

    resumed = resume_care_activity(care_activity_id=activity.id)
    assert resumed.status == CareActivityStatus.ACTIVE
    assert EventRecord.objects.filter(event_type="CareActivityResumed").count() == 1

    ended = end_care_activity(care_activity_id=activity.id)
    assert ended.status == CareActivityStatus.ENDED
    assert ScheduleDefinition.objects.get(pk=activity.schedule_definition_id).status == ScheduleStatus.CANCELLED
    assert EventRecord.objects.filter(event_type="CareActivityEnded").count() == 1


@pytest.mark.django_db
def test_prescription_shared_primary_key(elder, workflow_definition, recurrence_definition, schedule_start_at):
    prescription = create_prescription(
        elder_id=elder.id,
        workflow_definition_id=workflow_definition.id,
        recurrence_definition=recurrence_definition,
        timezone_name="UTC",
        start_at=schedule_start_at,
        display_title="Aspirin",
        medication_reference="med-aspirin",
        dosage_information="1 tablet",
        elder_friendly_description="Take your morning aspirin",
        media_reference=None,
    )
    assert prescription.pk == prescription.care_activity_id
    assert Prescription.objects.get(pk=prescription.pk).care_activity.activity_type == CareActivityType.MEDICATION
    assert EventRecord.objects.filter(event_type="PrescriptionCreated").count() == 1


@pytest.mark.django_db
def test_get_active_prescriptions(elder, workflow_definition, recurrence_definition, schedule_start_at):
    create_prescription(
        elder_id=elder.id,
        workflow_definition_id=workflow_definition.id,
        recurrence_definition=recurrence_definition,
        timezone_name="UTC",
        start_at=schedule_start_at,
        display_title="Vitamin D",
        medication_reference="med-vitd",
        dosage_information="1 capsule",
        elder_friendly_description="Take vitamin D",
    )
    active = get_active_prescriptions(elder_id=elder.id)
    assert len(active) == 1
    assert active[0].medication_reference == "med-vitd"


@pytest.mark.django_db
def test_occurrence_due_starts_workflow_via_care(
    elder,
    workflow_definition,
    recurrence_definition,
    schedule_start_at,
):
    activity = create_prescription(
        elder_id=elder.id,
        workflow_definition_id=workflow_definition.id,
        recurrence_definition=recurrence_definition,
        timezone_name="UTC",
        start_at=schedule_start_at,
        display_title="Evening pill",
        medication_reference="med-evening",
        dosage_information="1 tablet",
        elder_friendly_description="Evening medication",
    )
    occurrence = Occurrence.objects.filter(schedule_definition_id=activity.care_activity.schedule_definition_id).first()
    occurrence.status = OccurrenceStatus.SCHEDULED
    occurrence.scheduled_for = timezone.now() - timedelta(minutes=1)
    occurrence.save(update_fields=["status", "scheduled_for"])
    process_due_occurrences(now=timezone.now())

    event = EventRecord.objects.filter(event_type="OccurrenceDue").latest("recorded_at")
    execution = handle_occurrence_due_event(event_id=event.id)
    assert execution.status == ExecutionStatus.ACTIVE
    assert execution.workflow_definition_id == workflow_definition.id
    assert WorkflowExecution.objects.filter(occurrence_id=occurrence.id).count() == 1


@pytest.mark.django_db
def test_medication_taken_from_execution_confirmed(
    elder,
    workflow_definition,
    recurrence_definition,
    schedule_start_at,
):
    prescription = create_prescription(
        elder_id=elder.id,
        workflow_definition_id=workflow_definition.id,
        recurrence_definition=recurrence_definition,
        timezone_name="UTC",
        start_at=schedule_start_at,
        display_title="Morning pill",
        medication_reference="med-morning",
        dosage_information="1 tablet",
        elder_friendly_description="Morning medication",
    )
    occurrence = Occurrence.objects.filter(
        schedule_definition_id=prescription.care_activity.schedule_definition_id
    ).first()
    mark_occurrence_due(occurrence)
    execution = start_execution(
        occurrence_id=occurrence.id,
        workflow_definition_id=workflow_definition.id,
    )
    submit_direct_interaction_evidence(
        execution_id=execution.id,
        evidence_type="HUB_CONFIRMATION",
        interaction_reference="hub-confirm-care",
    )
    completion = interpret_execution_result(
        workflow_execution_id=execution.id,
        result_type=WorkflowExecutionResultType.EXECUTION_CONFIRMED,
    )
    assert completion.completion_state == CompletionState.MEDICATION_TAKEN
    assert EventRecord.objects.filter(event_type="MedicationTaken").count() == 1
    assert not EventRecord.objects.filter(event_type="MedicationTaken", producer="workflow").exists()


@pytest.mark.django_db
def test_medication_missed_from_execution_missed(
    elder,
    workflow_definition,
    recurrence_definition,
    schedule_start_at,
):
    prescription = create_prescription(
        elder_id=elder.id,
        workflow_definition_id=workflow_definition.id,
        recurrence_definition=recurrence_definition,
        timezone_name="UTC",
        start_at=schedule_start_at,
        display_title="Missed pill",
        medication_reference="med-missed",
        dosage_information="1 tablet",
        elder_friendly_description="Missed medication",
    )
    occurrence = Occurrence.objects.filter(
        schedule_definition_id=prescription.care_activity.schedule_definition_id
    ).first()
    mark_occurrence_due(occurrence)
    execution = start_execution(
        occurrence_id=occurrence.id,
        workflow_definition_id=workflow_definition.id,
    )
    completion = interpret_execution_result(
        workflow_execution_id=execution.id,
        result_type=WorkflowExecutionResultType.EXECUTION_MISSED,
    )
    assert completion.completion_state == CompletionState.MEDICATION_MISSED
    assert EventRecord.objects.filter(event_type="MedicationMissed").count() == 1


@pytest.mark.django_db
def test_general_activity_completed_event(
    elder,
    workflow_definition,
    recurrence_definition,
    schedule_start_at,
):
    activity = create_care_activity(
        elder_id=elder.id,
        activity_type=CareActivityType.DAILY_CHECK_IN,
        workflow_definition_id=workflow_definition.id,
        recurrence_definition=recurrence_definition,
        timezone_name="UTC",
        start_at=schedule_start_at,
        display_title="Daily check-in",
    )
    occurrence = Occurrence.objects.filter(schedule_definition_id=activity.schedule_definition_id).first()
    mark_occurrence_due(occurrence)
    execution = start_execution(
        occurrence_id=occurrence.id,
        workflow_definition_id=workflow_definition.id,
    )
    completion = interpret_execution_result(
        workflow_execution_id=execution.id,
        result_type=WorkflowExecutionResultType.EXECUTION_CONFIRMED,
    )
    assert completion.completion_state == CompletionState.CARE_ACTIVITY_COMPLETED
    assert EventRecord.objects.filter(event_type="CareActivityCompleted").count() == 1


@pytest.mark.django_db
def test_completion_idempotency(
    elder,
    workflow_definition,
    recurrence_definition,
    schedule_start_at,
):
    prescription = create_prescription(
        elder_id=elder.id,
        workflow_definition_id=workflow_definition.id,
        recurrence_definition=recurrence_definition,
        timezone_name="UTC",
        start_at=schedule_start_at,
        display_title="Idempotent pill",
        medication_reference="med-idem",
        dosage_information="1 tablet",
        elder_friendly_description="Idempotent medication",
    )
    occurrence = Occurrence.objects.filter(
        schedule_definition_id=prescription.care_activity.schedule_definition_id
    ).first()
    mark_occurrence_due(occurrence)
    execution = start_execution(
        occurrence_id=occurrence.id,
        workflow_definition_id=workflow_definition.id,
    )
    first = interpret_execution_result(
        workflow_execution_id=execution.id,
        result_type=WorkflowExecutionResultType.EXECUTION_CONFIRMED,
    )
    second = interpret_execution_result(
        workflow_execution_id=execution.id,
        result_type=WorkflowExecutionResultType.EXECUTION_CONFIRMED,
    )
    assert first.id == second.id
    assert CareCompletion.objects.count() == 1
    assert EventRecord.objects.filter(event_type="MedicationTaken").count() == 1


@pytest.mark.django_db
def test_updating_activity_does_not_rewrite_completion_history(
    elder,
    workflow_definition,
    recurrence_definition,
    schedule_start_at,
):
    prescription = create_prescription(
        elder_id=elder.id,
        workflow_definition_id=workflow_definition.id,
        recurrence_definition=recurrence_definition,
        timezone_name="UTC",
        start_at=schedule_start_at,
        display_title="History pill",
        medication_reference="med-history",
        dosage_information="1 tablet",
        elder_friendly_description="History medication",
    )
    activity_id = prescription.care_activity_id
    occurrence = Occurrence.objects.filter(
        schedule_definition_id=prescription.care_activity.schedule_definition_id
    ).first()
    mark_occurrence_due(occurrence)
    execution = start_execution(
        occurrence_id=occurrence.id,
        workflow_definition_id=workflow_definition.id,
    )
    completion = interpret_execution_result(
        workflow_execution_id=execution.id,
        result_type=WorkflowExecutionResultType.EXECUTION_CONFIRMED,
    )
    original_state = completion.completion_state
    original_interpreted_at = completion.interpreted_at

    update_care_activity(activity_id, display_title="Updated title")
    completion.refresh_from_db()
    assert completion.completion_state == original_state
    assert completion.interpreted_at == original_interpreted_at
    history = get_care_completion_history(care_activity_id=activity_id)
    assert len(history) == 1
    assert history[0].completion_state == CompletionState.MEDICATION_TAKEN


@pytest.mark.django_db
def test_care_does_not_calculate_recurrence(elder, workflow_definition, schedule_start_at):
    with patch("domains.scheduling.recurrence.engine.validate_recurrence_definition") as validate_mock:
        validate_mock.side_effect = lambda value: value
        create_care_activity(
            elder_id=elder.id,
            activity_type=CareActivityType.GENERAL,
            workflow_definition_id=workflow_definition.id,
            recurrence_definition={"type": "daily", "time": "09:00"},
            timezone_name="UTC",
            start_at=schedule_start_at,
            display_title="Opaque recurrence",
        )
    validate_mock.assert_called_once()


@pytest.mark.django_db
def test_care_does_not_own_workflow_execution(
    elder,
    workflow_definition,
    recurrence_definition,
    schedule_start_at,
):
    activity = create_care_activity(
        elder_id=elder.id,
        activity_type=CareActivityType.GENERAL,
        workflow_definition_id=workflow_definition.id,
        recurrence_definition=recurrence_definition,
        timezone_name="UTC",
        start_at=schedule_start_at,
        display_title="No execution ownership",
    )
    assert not hasattr(activity, "workflow_execution")
    assert WorkflowExecution.objects.count() == 0


@pytest.mark.django_db
def test_paused_activity_rejects_occurrence_due(
    elder,
    workflow_definition,
    recurrence_definition,
    schedule_start_at,
):
    activity = create_care_activity(
        elder_id=elder.id,
        activity_type=CareActivityType.GENERAL,
        workflow_definition_id=workflow_definition.id,
        recurrence_definition=recurrence_definition,
        timezone_name="UTC",
        start_at=schedule_start_at,
        display_title="Paused activity",
    )
    pause_care_activity(care_activity_id=activity.id)
    occurrence = Occurrence.objects.filter(schedule_definition_id=activity.schedule_definition_id).first()
    mark_occurrence_due(occurrence)
    event = EventRecord.objects.filter(event_type="OccurrenceDue").latest("recorded_at")
    with pytest.raises(InvalidCareActivityStateError):
        handle_occurrence_due_event(event_id=event.id)


@pytest.mark.django_db
def test_no_device_domain_installed():
    from django.apps import apps

    assert not apps.is_installed("domains.device")


@pytest.mark.django_db
def test_care_activity_stores_compartment_reference_only(
    elder,
    workflow_definition,
    recurrence_definition,
    schedule_start_at,
):
    activity = create_prescription(
        elder_id=elder.id,
        workflow_definition_id=workflow_definition.id,
        recurrence_definition=recurrence_definition,
        timezone_name="UTC",
        start_at=schedule_start_at,
        display_title="Pillbox med",
        medication_reference="med-pillbox",
        dosage_information="1 tablet",
        elder_friendly_description="Pillbox medication",
        compartment_assignment_reference="compartment:A1",
    )
    assert activity.care_activity.compartment_assignment_reference == "compartment:A1"
    activity_model = get_care_activity(activity.care_activity_id)
    assert activity_model.compartment_assignment_reference == "compartment:A1"
