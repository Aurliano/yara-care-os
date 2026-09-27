"""Tests for Sprint C3 — Workflow Runtime & Medication Execution."""

import uuid
from datetime import datetime, timedelta

import pytest
from django.utils import timezone

from domains.care.enums import CareActivityStatus, CareActivityType, CompletionState, WorkflowExecutionResultType
from domains.care.models import CareActivity, CareCompletion
from domains.care.services.activities import (
    create_care_activity,
    end_care_activity,
    pause_care_activity,
    resume_care_activity,
)
from domains.care.services.interpretation import interpret_execution_result
from domains.event.models import EventRecord
from domains.scheduling.enums import OccurrenceStatus, ScheduleExceptionType
from domains.scheduling.models import Occurrence
from domains.scheduling.services.occurrences import get_occurrence, skip_occurrence
from domains.scheduling.services.schedules import add_schedule_exception
from domains.workflow.enums import EvidenceSourceType, ExecutionStatus
from domains.workflow.identity import compute_execution_id
from domains.workflow.medication_reminder_policy import medication_reminder_definition
from domains.workflow.models import ConfirmationEvidence, WorkflowExecution
from domains.workflow.services.evidence import submit_confirmation_evidence, submit_direct_interaction_evidence
from domains.workflow.services.executions import (
    cancel_execution,
    create_workflow_definition,
    get_execution,
    start_execution,
)
from domains.workflow.services.postpone import postpone_execution
from domains.workflow.services.timeout import process_timed_out_execution


from domains.identity_access.services.profiles import create_elder, create_user


@pytest.fixture
def care_user(db):
    return create_user(
        phone="+989132222222",
        password="securepass123",
        full_name="Care Tester",
    )


@pytest.fixture
def elder(db, care_user):
    return create_elder(actor=care_user, full_name="Care Elder")


@pytest.fixture
def elder_id(elder) -> uuid.UUID:
    return elder.id


@pytest.fixture
def workflow_def():
    return create_workflow_definition(
        code="wf-c3-med-policy",
        name="C3 Medication Policy",
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
        display_title="Aspirin 100mg",
    )
    from domains.care.models import Prescription

    Prescription.objects.create(
        care_activity=activity,
        medication_reference="aspirin-100",
        dosage_information="1 tablet",
        elder_friendly_description="Take with water",
    )
    # Get the occurrence
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
def test_pause_care_activity_aborts_active_execution(care_activity_and_occurrence, workflow_def):
    activity, occurrence = care_activity_and_occurrence
    execution = start_execution(
        occurrence_id=occurrence.id,
        workflow_definition_id=workflow_def.id,
    )
    assert execution.status == ExecutionStatus.ACTIVE

    # Pause care activity
    paused_activity = pause_care_activity(care_activity_id=activity.id)
    assert paused_activity.status == CareActivityStatus.PAUSED

    # Execution must be aborted immediately
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.CANCELLED
    assert execution.completed_at is not None

    # Idempotent cancel
    cancel_execution(execution_id=execution.id)
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.CANCELLED


@pytest.mark.django_db
def test_end_care_activity_aborts_active_execution(care_activity_and_occurrence, workflow_def):
    activity, occurrence = care_activity_and_occurrence
    execution = start_execution(
        occurrence_id=occurrence.id,
        workflow_definition_id=workflow_def.id,
    )
    assert execution.status == ExecutionStatus.ACTIVE

    # End care activity
    ended_activity = end_care_activity(care_activity_id=activity.id)
    assert ended_activity.status == CareActivityStatus.ENDED

    # Execution must be aborted immediately
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.CANCELLED
    assert execution.completed_at is not None


@pytest.mark.django_db
def test_skip_current_occurrence_aborts_active_execution(care_activity_and_occurrence, workflow_def):
    activity, occurrence = care_activity_and_occurrence
    execution = start_execution(
        occurrence_id=occurrence.id,
        workflow_definition_id=workflow_def.id,
    )
    assert execution.status == ExecutionStatus.ACTIVE

    # Skip current occurrence
    skipped = skip_occurrence(occurrence_id=occurrence.id)
    assert skipped.status == OccurrenceStatus.SKIPPED

    # Execution must be aborted immediately
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.CANCELLED


@pytest.mark.django_db
def test_postpone_does_not_mutate_occurrence_and_is_idempotent(care_activity_and_occurrence, workflow_def):
    activity, occurrence = care_activity_and_occurrence
    execution = start_execution(
        occurrence_id=occurrence.id,
        workflow_definition_id=workflow_def.id,
    )
    original_scheduled_for = occurrence.scheduled_for

    # Postpone with request id
    postpone_req_id = "postpone-uuid-1"
    postponed_exec = postpone_execution(
        execution_id=execution.id,
        postpone_request_id=postpone_req_id,
    )
    assert postponed_exec.postpone_count == 1
    assert postponed_exec.active_until > timezone.now()

    # Invariant: Occurrence.scheduled_for MUST NOT be mutated!
    occurrence.refresh_from_db()
    assert occurrence.scheduled_for == original_scheduled_for

    # Idempotent retry with same request ID
    retry_exec = postpone_execution(
        execution_id=execution.id,
        postpone_request_id=postpone_req_id,
    )
    assert retry_exec.postpone_count == 1
    assert retry_exec.id == execution.id

    # Second postpone with different request id
    second_req_id = "postpone-uuid-2"
    second_exec = postpone_execution(
        execution_id=execution.id,
        postpone_request_id=second_req_id,
    )
    assert second_exec.postpone_count == 2

    # Third postpone exceeds max_count = 2
    from domains.workflow.exceptions import PostponeNotAllowedError

    with pytest.raises(PostponeNotAllowedError, match="Maximum postpone count reached"):
        postpone_execution(
            execution_id=execution.id,
            postpone_request_id="postpone-uuid-3",
        )


@pytest.mark.django_db
def test_reschedule_exception_cancels_active_execution(care_activity_and_occurrence, workflow_def):
    activity, occurrence = care_activity_and_occurrence
    execution = start_execution(
        occurrence_id=occurrence.id,
        workflow_definition_id=workflow_def.id,
    )
    assert execution.status == ExecutionStatus.ACTIVE
    original_occurrence_id = occurrence.id

    # Reschedule occurrence to tomorrow
    tomorrow = timezone.now() + timedelta(days=1)
    add_schedule_exception(
        schedule_definition_id=activity.schedule_definition_id,
        original_time=occurrence.scheduled_for,
        exception_type=ScheduleExceptionType.RESCHEDULE,
        replacement_time=tomorrow,
    )

    # Active execution was cancelled immediately
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.CANCELLED

    # Occurrence scheduled_for updated in-place without changing identity (no duplicate)
    occurrence.refresh_from_db()
    assert occurrence.id == original_occurrence_id
    assert occurrence.scheduled_for == tomorrow
    assert occurrence.status == OccurrenceStatus.SCHEDULED
    # Evidence and execution still link to the same occurrence ID
    assert execution.occurrence_id == occurrence.id


@pytest.mark.django_db
def test_physical_confirmation_exception_supersedes_administrative_abort(
    care_activity_and_occurrence, workflow_def
):
    activity, occurrence = care_activity_and_occurrence
    execution = start_execution(
        occurrence_id=occurrence.id,
        workflow_definition_id=workflow_def.id,
    )
    assert execution.status == ExecutionStatus.ACTIVE

    # Administratively pause care activity -> execution cancelled
    pause_care_activity(care_activity_id=activity.id)
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.CANCELLED

    # Cloud interprets the cancellation
    completion = interpret_execution_result(
        workflow_execution_id=execution.id,
        result_type=WorkflowExecutionResultType.EXECUTION_CANCELLED,
    )
    assert completion.completion_state == CompletionState.CARE_ACTIVITY_CANCELLED
    assert CareCompletion.objects.filter(workflow_execution_id=execution.id).count() == 1

    # Physical confirmation arrives from Hub (elder took dose before pause command arrived)
    confirmed_exec = submit_direct_interaction_evidence(
        execution_id=execution.id,
        evidence_type="HUB_CONFIRMATION",
        interaction_reference="hub_screen_confirm_physical",
    )
    assert confirmed_exec.status == ExecutionStatus.CONFIRMED

    # Care interpretation upgrades the cancelled completion to MEDICATION_TAKEN
    upgraded_completion = interpret_execution_result(
        workflow_execution_id=execution.id,
        result_type=WorkflowExecutionResultType.EXECUTION_CONFIRMED,
    )
    assert upgraded_completion.id == completion.id
    assert upgraded_completion.completion_state == CompletionState.MEDICATION_TAKEN
    # Invariant: exactly ONE CareCompletion row exists (no competing CARE_ACTIVITY_CANCELLED row)
    assert CareCompletion.objects.filter(workflow_execution_id=execution.id).count() == 1
    assert not CareCompletion.objects.filter(
        workflow_execution_id=execution.id,
        completion_state=CompletionState.CARE_ACTIVITY_CANCELLED,
    ).exists()


@pytest.mark.django_db
def test_duplicate_confirmation_evidence_is_idempotent_no_duplicate_completion(
    care_activity_and_occurrence, workflow_def
):
    activity, occurrence = care_activity_and_occurrence
    execution = start_execution(
        occurrence_id=occurrence.id,
        workflow_definition_id=workflow_def.id,
    )

    # First confirmation
    submit_direct_interaction_evidence(
        execution_id=execution.id,
        evidence_type="HUB_CONFIRMATION",
        interaction_reference="btn-confirm-1",
    )
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.CONFIRMED

    completion1 = interpret_execution_result(
        workflow_execution_id=execution.id,
        result_type=WorkflowExecutionResultType.EXECUTION_CONFIRMED,
    )
    assert completion1.completion_state == CompletionState.MEDICATION_TAKEN

    # Duplicate confirmation evidence submission
    submit_direct_interaction_evidence(
        execution_id=execution.id,
        evidence_type="HUB_CONFIRMATION",
        interaction_reference="btn-confirm-1",
    )
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.CONFIRMED

    completion2 = interpret_execution_result(
        workflow_execution_id=execution.id,
        result_type=WorkflowExecutionResultType.EXECUTION_CONFIRMED,
    )
    assert completion2.id == completion1.id
    assert CareCompletion.objects.filter(workflow_execution_id=execution.id).count() == 1


@pytest.mark.django_db
def test_offline_timeout_retry_escalation_and_final_missed(care_activity_and_occurrence, workflow_def):
    activity, occurrence = care_activity_and_occurrence
    execution = start_execution(
        occurrence_id=occurrence.id,
        workflow_definition_id=workflow_def.id,
    )
    assert execution.status == ExecutionStatus.ACTIVE
    assert execution.retry_count == 0
    assert execution.escalation_index == 0

    # Timeout 1: Retry 1
    execution.active_until = timezone.now() - timedelta(seconds=1)
    execution.save(update_fields=["active_until"])
    process_timed_out_execution(execution)
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.ACTIVE
    assert execution.retry_count == 1

    # Timeout 2: Retry 2
    execution.active_until = timezone.now() - timedelta(seconds=1)
    execution.save(update_fields=["active_until"])
    process_timed_out_execution(execution)
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.ACTIVE
    assert execution.retry_count == 2
    assert execution.escalation_index == 0

    # Timeout 3: Escalation 1 (NOTIFY_CAREGIVER)
    execution.active_until = timezone.now() - timedelta(seconds=1)
    execution.save(update_fields=["active_until"])
    process_timed_out_execution(execution)
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.ACTIVE
    assert execution.escalation_index == 1
    assert execution.current_action["type"] == "NOTIFY_CAREGIVER"

    # Timeout 4: Final timeout -> MISSED
    execution.active_until = timezone.now() - timedelta(seconds=1)
    execution.save(update_fields=["active_until"])
    process_timed_out_execution(execution)
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.MISSED
    assert execution.completed_at is not None

    # Interpret missed execution
    missed_completion = interpret_execution_result(
        workflow_execution_id=execution.id,
        result_type=WorkflowExecutionResultType.EXECUTION_MISSED,
    )
    assert missed_completion.completion_state == CompletionState.MEDICATION_MISSED


@pytest.mark.django_db
def test_timeout_concurrency_locking_prevents_duplicate_transition(care_activity_and_occurrence, workflow_def):
    activity, occurrence = care_activity_and_occurrence
    execution = start_execution(
        occurrence_id=occurrence.id,
        workflow_definition_id=workflow_def.id,
    )
    assert execution.retry_count == 0

    now_timeout = timezone.now()
    execution.active_until = now_timeout - timedelta(seconds=1)
    execution.save(update_fields=["active_until"])

    # Worker 1 processes timeout at now_timeout
    process_timed_out_execution(execution, now=now_timeout)
    execution.refresh_from_db()
    assert execution.retry_count == 1
    first_active_until = execution.active_until
    assert first_active_until > now_timeout

    # Worker 2 attempts duplicate processing for the same logical timeout boundary
    process_timed_out_execution(execution, now=now_timeout)
    execution.refresh_from_db()

    # Guard invariant: Exactly ONE transition occurred (0 -> 1, not 0 -> 2)
    assert execution.retry_count == 1
    assert execution.active_until == first_active_until

