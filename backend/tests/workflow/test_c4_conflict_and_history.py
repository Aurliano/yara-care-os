"""Tests for Sprint C4 — Conflict Resolution & Medication History."""

import uuid
from datetime import datetime, timedelta

import pytest
from django.utils import timezone

from domains.care.enums import CareActivityStatus, CareActivityType, CompletionState, WorkflowExecutionResultType
from domains.care.models import CareActivity, CareCompletion, Prescription
from domains.care.services.activities import (
    create_care_activity,
    end_care_activity,
    get_elder_care_activities,
    pause_care_activity,
    resume_care_activity,
)
from domains.care.services.interpretation import get_care_completion_history, interpret_execution_result
from domains.care.services.prescriptions import (
    create_prescription,
    get_active_prescriptions,
    get_history_prescriptions,
)
from domains.identity_access.services.profiles import create_elder, create_user
from domains.scheduling.enums import OccurrenceStatus, ScheduleExceptionType
from domains.scheduling.exceptions import InvalidOccurrenceStateError, InvalidScheduleStateError
from domains.scheduling.models import Occurrence
from domains.scheduling.services.occurrences import cancel_occurrence, get_occurrence, skip_occurrence
from domains.scheduling.services.schedules import add_schedule_exception
from domains.workflow.enums import EvidenceSourceType, ExecutionStatus
from domains.workflow.medication_reminder_policy import medication_reminder_definition
from domains.workflow.models import ConfirmationEvidence, WorkflowExecution
from domains.workflow.services.evidence import submit_confirmation_evidence, submit_direct_interaction_evidence
from domains.workflow.services.executions import (
    cancel_execution,
    create_workflow_definition,
    get_execution,
    start_execution,
)
from domains.workflow.services.timeout import process_timed_out_execution


@pytest.fixture
def care_user(db):
    return create_user(
        phone="+989133333333",
        password="securepass123",
        full_name="C4 Care Tester",
    )


@pytest.fixture
def elder(db, care_user):
    return create_elder(actor=care_user, full_name="C4 Elder")


@pytest.fixture
def elder_id(elder) -> uuid.UUID:
    return elder.id


@pytest.fixture
def workflow_def():
    return create_workflow_definition(
        code=f"wf-c4-policy-{uuid.uuid4().hex[:6]}",
        name="C4 Medication Policy",
        definition=medication_reminder_definition(),
    )


@pytest.fixture
def care_activity_and_occurrence(db, elder_id, workflow_def):
    now = timezone.now().replace(microsecond=0)
    activity = create_care_activity(
        elder_id=elder_id,
        activity_type=CareActivityType.MEDICATION,
        workflow_definition_id=workflow_def.id,
        recurrence_definition={"type": "daily", "times": [now.strftime("%H:%M")]},
        timezone_name="UTC",
        start_at=now - timedelta(minutes=10),
        display_title="Atorvastatin 20mg",
    )
    Prescription.objects.create(
        care_activity=activity,
        medication_reference="atorvastatin-20",
        dosage_information="1 tablet",
        elder_friendly_description="Take at bedtime",
    )
    occurrence = Occurrence.objects.filter(
        schedule_definition_id=activity.schedule_definition_id
    ).order_by("scheduled_for").first()
    if occurrence is None:
        occurrence = Occurrence.objects.create(
            id=uuid.uuid4(),
            schedule_definition=activity.schedule_definition,
            scheduled_for=now,
            status=OccurrenceStatus.DUE,
        )
    else:
        occurrence.status = OccurrenceStatus.DUE
        occurrence.save(update_fields=["status"])
    return activity, occurrence


@pytest.mark.django_db
def test_c01_family_skip_vs_hub_confirm_physical_wins(care_activity_and_occurrence, workflow_def):
    """C-01 / Scenario A: If dose is confirmed on Hub, subsequent skip is rejected and CONFIRMED wins."""
    activity, occurrence = care_activity_and_occurrence
    execution = start_execution(
        occurrence_id=occurrence.id,
        workflow_definition_id=workflow_def.id,
    )
    assert execution.status == ExecutionStatus.ACTIVE

    # Elder physically confirms dose on Hub
    submit_direct_interaction_evidence(
        execution_id=execution.id,
        evidence_type="HUB_CONFIRMATION",
        interaction_reference="hub-btn-1",
    )
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.CONFIRMED

    # Interpret execution result
    completion = interpret_execution_result(
        workflow_execution_id=execution.id,
        result_type=WorkflowExecutionResultType.EXECUTION_CONFIRMED,
    )
    assert completion.completion_state == CompletionState.MEDICATION_TAKEN

    # Family tries to SKIP an already confirmed dose -> must raise 409 Conflict
    with pytest.raises(InvalidOccurrenceStateError, match="completed execution"):
        skip_occurrence(occurrence_id=occurrence.id)

    # Invariants preserved
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.CONFIRMED
    assert CareCompletion.objects.filter(workflow_execution_id=execution.id).count() == 1
    assert CareCompletion.objects.get(workflow_execution_id=execution.id).completion_state == CompletionState.MEDICATION_TAKEN


@pytest.mark.django_db
def test_c02_family_pause_vs_hub_confirm_offline_physical_wins(care_activity_and_occurrence, workflow_def):
    """C-02: Family pauses plan while offline Hub confirms. Physical confirmation upgrades execution and completion."""
    activity, occurrence = care_activity_and_occurrence
    execution = start_execution(
        occurrence_id=occurrence.id,
        workflow_definition_id=workflow_def.id,
    )
    assert execution.status == ExecutionStatus.ACTIVE

    # Family pauses plan before Hub sync arrives
    pause_care_activity(care_activity_id=activity.id)
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.CANCELLED

    cancel_comp = interpret_execution_result(
        workflow_execution_id=execution.id,
        result_type=WorkflowExecutionResultType.EXECUTION_CANCELLED,
    )
    assert cancel_comp.completion_state == CompletionState.CARE_ACTIVITY_CANCELLED

    # Physical confirmation arrives from Hub
    submit_direct_interaction_evidence(
        execution_id=execution.id,
        evidence_type="HUB_CONFIRMATION",
        interaction_reference="hub-offline-dose-taken",
    )
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.CONFIRMED

    # Interpret upgrades completion in-place
    upgraded_comp = interpret_execution_result(
        workflow_execution_id=execution.id,
        result_type=WorkflowExecutionResultType.EXECUTION_CONFIRMED,
    )
    assert upgraded_comp.id == cancel_comp.id
    assert upgraded_comp.completion_state == CompletionState.MEDICATION_TAKEN

    # Activity remains PAUSED for future doses
    activity.refresh_from_db()
    assert activity.status == CareActivityStatus.PAUSED
    assert CareCompletion.objects.filter(workflow_execution_id=execution.id).count() == 1


@pytest.mark.django_db
def test_c03_family_end_vs_hub_confirm_plan_ends_dose_confirmed(care_activity_and_occurrence, workflow_def):
    """C-03 / Scenario B: Family ENDs plan while Hub physically confirms. Dose remains confirmed, plan remains ended."""
    activity, occurrence = care_activity_and_occurrence
    execution = start_execution(
        occurrence_id=occurrence.id,
        workflow_definition_id=workflow_def.id,
    )

    # Elder confirmed dose
    submit_direct_interaction_evidence(
        execution_id=execution.id,
        evidence_type="HUB_CONFIRMATION",
        interaction_reference="btn-confirm",
    )
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.CONFIRMED

    # Family ends the plan
    end_care_activity(care_activity_id=activity.id)
    activity.refresh_from_db()
    assert activity.status == CareActivityStatus.ENDED

    # Confirmed execution is not downgraded or cancelled
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.CONFIRMED

    comp = interpret_execution_result(
        workflow_execution_id=execution.id,
        result_type=WorkflowExecutionResultType.EXECUTION_CONFIRMED,
    )
    assert comp.completion_state == CompletionState.MEDICATION_TAKEN


@pytest.mark.django_db
def test_c04_family_reschedule_vs_hub_confirm_cannot_reschedule_completed(
    care_activity_and_occurrence, workflow_def
):
    """C-04 / Scenario E: Rescheduling an already completed occurrence is rejected; completed history is preserved."""
    activity, occurrence = care_activity_and_occurrence
    execution = start_execution(
        occurrence_id=occurrence.id,
        workflow_definition_id=workflow_def.id,
    )

    submit_direct_interaction_evidence(
        execution_id=execution.id,
        evidence_type="HUB_CONFIRMATION",
        interaction_reference="btn-confirm",
    )
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.CONFIRMED

    # Caregiver attempts to reschedule this already confirmed dose
    tomorrow = timezone.now() + timedelta(days=1)
    with pytest.raises(InvalidScheduleStateError, match="completed execution"):
        add_schedule_exception(
            schedule_definition_id=activity.schedule_definition_id,
            original_time=occurrence.scheduled_for,
            exception_type=ScheduleExceptionType.RESCHEDULE,
            replacement_time=tomorrow,
        )

    # Confirmed execution remains intact
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.CONFIRMED


@pytest.mark.django_db
def test_c05_family_skip_vs_hub_missed_cannot_skip_missed_dose(care_activity_and_occurrence, workflow_def):
    """C-05: If dose timed out to MISSED, subsequent SKIP is rejected; historical MISSED outcome is preserved."""
    activity, occurrence = care_activity_and_occurrence
    execution = start_execution(
        occurrence_id=occurrence.id,
        workflow_definition_id=workflow_def.id,
    )

    # Simulate timeout to MISSED (retries and escalation exhausted)
    execution.retry_count = 2
    execution.escalation_index = 1
    execution.active_until = timezone.now() - timedelta(seconds=1)
    execution.save()
    process_timed_out_execution(execution)
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.MISSED

    interpret_execution_result(
        workflow_execution_id=execution.id,
        result_type=WorkflowExecutionResultType.EXECUTION_MISSED,
    )

    # Family tries to SKIP an already missed dose
    with pytest.raises(InvalidOccurrenceStateError, match="completed execution"):
        skip_occurrence(occurrence_id=occurrence.id)

    # Outcome remains MEDICATION_MISSED
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.MISSED
    comp = CareCompletion.objects.get(workflow_execution_id=execution.id)
    assert comp.completion_state == CompletionState.MEDICATION_MISSED


@pytest.mark.django_db
def test_c06_family_end_vs_hub_missed_no_contradictory_outcomes(care_activity_and_occurrence, workflow_def):
    """C-06 / Scenario C: Family ENDs plan after dose became MISSED. History preserved, exactly one completion."""
    activity, occurrence = care_activity_and_occurrence
    execution = start_execution(
        occurrence_id=occurrence.id,
        workflow_definition_id=workflow_def.id,
    )

    execution.retry_count = 2
    execution.escalation_index = 1
    execution.active_until = timezone.now() - timedelta(seconds=1)
    execution.save()
    process_timed_out_execution(execution)
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.MISSED

    comp = interpret_execution_result(
        workflow_execution_id=execution.id,
        result_type=WorkflowExecutionResultType.EXECUTION_MISSED,
    )
    assert comp.completion_state == CompletionState.MEDICATION_MISSED

    # Family ends care activity
    end_care_activity(care_activity_id=activity.id)
    activity.refresh_from_db()
    assert activity.status == CareActivityStatus.ENDED

    # Historical execution remains MISSED
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.MISSED
    assert CareCompletion.objects.filter(workflow_execution_id=execution.id).count() == 1
    assert CareCompletion.objects.get(workflow_execution_id=execution.id).completion_state == CompletionState.MEDICATION_MISSED


@pytest.mark.django_db
def test_c07_c09_duplicate_skip_is_idempotent(care_activity_and_occurrence):
    """C-07 / C-09 / Scenario D: Repeated SKIP calls return same occurrence idempotently without error."""
    activity, occurrence = care_activity_and_occurrence
    first_skip = skip_occurrence(occurrence_id=occurrence.id)
    assert first_skip.status == OccurrenceStatus.SKIPPED

    # Duplicate skip
    second_skip = skip_occurrence(occurrence_id=occurrence.id)
    assert second_skip.status == OccurrenceStatus.SKIPPED
    assert second_skip.id == first_skip.id


@pytest.mark.django_db
def test_c08_duplicate_confirm_is_idempotent_single_care_completion(
    care_activity_and_occurrence, workflow_def
):
    """C-08: Duplicate physical confirmation evidence is idempotent and yields exactly one CareCompletion."""
    activity, occurrence = care_activity_and_occurrence
    execution = start_execution(
        occurrence_id=occurrence.id,
        workflow_definition_id=workflow_def.id,
    )

    submit_direct_interaction_evidence(
        execution_id=execution.id,
        evidence_type="HUB_CONFIRMATION",
        interaction_reference="btn-confirm-x",
    )
    comp1 = interpret_execution_result(
        workflow_execution_id=execution.id,
        result_type=WorkflowExecutionResultType.EXECUTION_CONFIRMED,
    )

    # Second identical confirmation
    submit_direct_interaction_evidence(
        execution_id=execution.id,
        evidence_type="HUB_CONFIRMATION",
        interaction_reference="btn-confirm-x",
    )
    comp2 = interpret_execution_result(
        workflow_execution_id=execution.id,
        result_type=WorkflowExecutionResultType.EXECUTION_CONFIRMED,
    )

    assert comp1.id == comp2.id
    assert CareCompletion.objects.filter(workflow_execution_id=execution.id).count() == 1


@pytest.mark.django_db
def test_c10_administrative_pause_resume_end_retries_are_idempotent(care_activity_and_occurrence):
    """C-10: Repeated administrative mutations (PAUSE, RESUME, END) are idempotent on client retry."""
    activity, _ = care_activity_and_occurrence

    # Pause twice
    p1 = pause_care_activity(care_activity_id=activity.id)
    p2 = pause_care_activity(care_activity_id=activity.id)
    assert p1.status == CareActivityStatus.PAUSED
    assert p2.status == CareActivityStatus.PAUSED

    # Resume twice
    r1 = resume_care_activity(care_activity_id=activity.id)
    r2 = resume_care_activity(care_activity_id=activity.id)
    assert r1.status == CareActivityStatus.ACTIVE
    assert r2.status == CareActivityStatus.ACTIVE

    # End twice
    e1 = end_care_activity(care_activity_id=activity.id)
    e2 = end_care_activity(care_activity_id=activity.id)
    assert e1.status == CareActivityStatus.ENDED
    assert e2.status == CareActivityStatus.ENDED


@pytest.mark.django_db
def test_dm17_active_vs_history_semantics(elder_id, workflow_def):
    """DM-17: Active plans includes ACTIVE + PAUSED. History includes ENDED + CANCELLED. Dose history preserved."""
    now = timezone.now()

    # Create 3 activities: active, paused, ended
    act_active = create_care_activity(
        elder_id=elder_id,
        activity_type=CareActivityType.MEDICATION,
        workflow_definition_id=workflow_def.id,
        recurrence_definition={"type": "daily", "times": ["08:00"]},
        timezone_name="UTC",
        start_at=now,
        display_title="Med 1 Active",
    )
    Prescription.objects.create(care_activity=act_active, medication_reference="med-1", dosage_information="1 tab")

    act_paused = create_care_activity(
        elder_id=elder_id,
        activity_type=CareActivityType.MEDICATION,
        workflow_definition_id=workflow_def.id,
        recurrence_definition={"type": "daily", "times": ["12:00"]},
        timezone_name="UTC",
        start_at=now,
        display_title="Med 2 Paused",
    )
    Prescription.objects.create(care_activity=act_paused, medication_reference="med-2", dosage_information="1 tab")
    pause_care_activity(care_activity_id=act_paused.id)

    act_ended = create_care_activity(
        elder_id=elder_id,
        activity_type=CareActivityType.MEDICATION,
        workflow_definition_id=workflow_def.id,
        recurrence_definition={"type": "daily", "times": ["20:00"]},
        timezone_name="UTC",
        start_at=now,
        display_title="Med 3 Ended",
    )
    Prescription.objects.create(care_activity=act_ended, medication_reference="med-3", dosage_information="1 tab")
    end_care_activity(care_activity_id=act_ended.id)

    # DM-17 invariant: Active plans must include both ACTIVE and PAUSED
    active_plans = get_active_prescriptions(elder_id=elder_id)
    active_ids = {p.care_activity_id for p in active_plans}
    assert act_active.id in active_ids
    assert act_paused.id in active_ids
    assert act_ended.id not in active_ids

    # DM-17 invariant: History plans include ENDED
    history_plans = get_history_prescriptions(elder_id=elder_id)
    history_ids = {p.care_activity_id for p in history_plans}
    assert act_ended.id in history_ids
    assert act_active.id not in history_ids
    assert act_paused.id not in history_ids
