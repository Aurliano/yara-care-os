from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from domains.event.models import EventRecord
from domains.scheduling.models import Occurrence
from domains.workflow.enums import ExecutionStatus
from domains.workflow.evidence_types import APPROVED_EVIDENCE_TYPES
from domains.workflow.exceptions import (
    EscalationNotAllowedError,
    InvalidDefinitionError,
    InvalidEvidenceError,
    PostponeNotAllowedError,
    WorkflowDefinitionConflictError,
)
from domains.workflow.identity import compute_execution_id
from domains.workflow.models import ActionResult, WorkflowExecution
from domains.workflow.services.actions import advance_escalation, report_action_result
from domains.workflow.services.evidence import submit_direct_interaction_evidence, submit_domain_event_evidence
from domains.workflow.services.executions import cancel_execution, create_workflow_definition, start_execution
from domains.workflow.services.postpone import postpone_execution
from domains.workflow.services.timeout import process_timed_out_execution
from tests.workflow.conftest import _base_definition, start_due_execution

HUB_CONFIRMATION = "HUB_CONFIRMATION"
COMPARTMENT_CLOSED = "COMPARTMENT_CLOSED"


@pytest.mark.django_db
def test_start_execution_requires_explicit_workflow_definition_id(due_occurrence):
    with pytest.raises(TypeError):
        start_execution(occurrence_id=due_occurrence.id)


@pytest.mark.django_db
def test_start_execution_creates_active_execution(due_occurrence, workflow_definition):
    execution = start_due_execution(due_occurrence, workflow_definition)
    assert execution.status == ExecutionStatus.ACTIVE
    assert execution.id == compute_execution_id(occurrence_id=due_occurrence.id)
    assert execution.workflow_definition_id == workflow_definition.id
    assert EventRecord.objects.filter(event_type="ExecutionStarted").count() == 1


@pytest.mark.django_db
def test_duplicate_start_execution_is_idempotent(due_occurrence, workflow_definition):
    first = start_due_execution(due_occurrence, workflow_definition)
    second = start_due_execution(due_occurrence, workflow_definition)
    assert first.id == second.id
    assert WorkflowExecution.objects.count() == 1
    assert EventRecord.objects.filter(event_type="ExecutionStarted").count() == 1


@pytest.mark.django_db
def test_conflicting_workflow_definition_is_rejected(due_occurrence, workflow_definition):
    start_due_execution(due_occurrence, workflow_definition)
    other = create_workflow_definition(
        code="wf-other",
        name="Other Workflow",
        definition=_base_definition(),
    )
    with pytest.raises(WorkflowDefinitionConflictError):
        start_execution(occurrence_id=due_occurrence.id, workflow_definition_id=other.id)


@pytest.mark.django_db
def test_one_execution_per_occurrence(due_occurrence, workflow_definition):
    start_due_execution(due_occurrence, workflow_definition)
    assert WorkflowExecution.objects.filter(occurrence_id=due_occurrence.id).count() == 1


@pytest.mark.django_db
def test_terminal_execution_cannot_reactivate(due_occurrence, workflow_definition):
    execution = start_due_execution(due_occurrence, workflow_definition)
    submit_direct_interaction_evidence(
        execution_id=execution.id,
        evidence_type=HUB_CONFIRMATION,
        interaction_reference="hub-1",
    )
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.CONFIRMED
    again = start_due_execution(due_occurrence, workflow_definition)
    assert again.status == ExecutionStatus.CONFIRMED


@pytest.mark.django_db
def test_valid_evidence_confirms_execution(due_occurrence, workflow_definition):
    execution = start_due_execution(due_occurrence, workflow_definition)
    confirmed = submit_direct_interaction_evidence(
        execution_id=execution.id,
        evidence_type=HUB_CONFIRMATION,
        interaction_reference="hub-confirm-1",
    )
    assert confirmed.status == ExecutionStatus.CONFIRMED
    assert EventRecord.objects.filter(event_type="ExecutionConfirmed").count() == 1


@pytest.mark.django_db
def test_invalid_evidence_rejected(due_occurrence, workflow_definition):
    execution = start_due_execution(due_occurrence, workflow_definition)
    with pytest.raises(InvalidEvidenceError):
        submit_direct_interaction_evidence(
            execution_id=execution.id,
            evidence_type=COMPARTMENT_CLOSED,
            interaction_reference="bad-1",
        )


@pytest.mark.django_db
def test_unapproved_evidence_type_rejected_in_definition():
    with pytest.raises(InvalidDefinitionError):
        _base_definition(confirmation_policy={"accepted_evidence_types": ["VOICE_CONFIRMED"]})


@pytest.mark.django_db
def test_approved_evidence_types_are_documented_not_closed_enum():
    assert HUB_CONFIRMATION in APPROVED_EVIDENCE_TYPES
    assert "VOICE_CONFIRMED" not in APPROVED_EVIDENCE_TYPES


@pytest.mark.django_db
def test_duplicate_evidence_is_idempotent(due_occurrence, workflow_definition):
    execution = start_due_execution(due_occurrence, workflow_definition)
    submit_direct_interaction_evidence(
        execution_id=execution.id,
        evidence_type=HUB_CONFIRMATION,
        interaction_reference="dup-1",
    )
    second = submit_direct_interaction_evidence(
        execution_id=execution.id,
        evidence_type=HUB_CONFIRMATION,
        interaction_reference="dup-1",
    )
    assert second.status == ExecutionStatus.CONFIRMED
    assert EventRecord.objects.filter(event_type="ExecutionConfirmed").count() == 1


@pytest.mark.django_db
def test_domain_event_evidence_path(due_occurrence):
    wf = create_workflow_definition(
        code=f"wf-device-{due_occurrence.id.hex[:6]}",
        name="Device WF",
        definition=_base_definition(
            confirmation_policy={"accepted_evidence_types": [COMPARTMENT_CLOSED]}
        ),
    )
    execution = start_execution(occurrence_id=due_occurrence.id, workflow_definition_id=wf.id)
    confirmed = submit_domain_event_evidence(
        execution_id=execution.id,
        evidence_type=COMPARTMENT_CLOSED,
        event_reference="device-event-1",
    )
    assert confirmed.status == ExecutionStatus.CONFIRMED


@pytest.mark.django_db
def test_confirm_rolls_back_when_event_recording_fails(due_occurrence, workflow_definition):
    execution = start_due_execution(due_occurrence, workflow_definition)
    with patch(
        "domains.workflow.services.events.record_event",
        side_effect=RuntimeError("event recording failed"),
    ):
        with pytest.raises(RuntimeError):
            submit_direct_interaction_evidence(
                execution_id=execution.id,
                evidence_type=HUB_CONFIRMATION,
                interaction_reference="rollback-1",
            )
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.ACTIVE
    assert EventRecord.objects.filter(event_type="ExecutionConfirmed").count() == 0


@pytest.mark.django_db
def test_postpone_policy(due_occurrence, workflow_definition):
    execution = start_due_execution(due_occurrence, workflow_definition)
    before = execution.active_until
    postponed = postpone_execution(execution_id=execution.id)
    assert postponed.postpone_count == 1
    assert postponed.active_until > before
    assert EventRecord.objects.filter(event_type="ExecutionPostponed").count() == 1


@pytest.mark.django_db
def test_postpone_respects_max_count(due_occurrence, workflow_definition):
    execution = start_due_execution(due_occurrence, workflow_definition)
    postpone_execution(execution_id=execution.id)
    postpone_execution(execution_id=execution.id)
    with pytest.raises(PostponeNotAllowedError):
        postpone_execution(execution_id=execution.id)


@pytest.mark.django_db
def test_retry_on_timeout(due_occurrence, workflow_definition):
    execution = start_due_execution(due_occurrence, workflow_definition)
    execution.active_until = timezone.now() - timedelta(seconds=1)
    execution.save(update_fields=["active_until"])
    process_timed_out_execution(execution)
    execution.refresh_from_db()
    assert execution.retry_count == 1
    assert execution.status == ExecutionStatus.ACTIVE


@pytest.mark.django_db
def test_duplicate_timeout_processing_does_not_double_retry(due_occurrence, workflow_definition):
    execution = start_due_execution(due_occurrence, workflow_definition)
    execution.active_until = timezone.now() - timedelta(seconds=1)
    execution.save(update_fields=["active_until"])
    process_timed_out_execution(execution)
    execution.refresh_from_db()
    first_retry = execution.retry_count
    process_timed_out_execution(execution)
    execution.refresh_from_db()
    assert execution.retry_count == first_retry


@pytest.mark.django_db
def test_escalation_follows_definition_order(due_occurrence, workflow_definition):
    execution = start_due_execution(due_occurrence, workflow_definition)
    execution.retry_count = 1
    execution.active_until = timezone.now() - timedelta(seconds=1)
    execution.save(update_fields=["retry_count", "active_until"])
    process_timed_out_execution(execution)
    execution.refresh_from_db()
    assert execution.escalation_index == 1
    assert execution.current_action["type"] == "NOTIFY_CAREGIVER"
    assert EventRecord.objects.filter(event_type="EscalationTriggered").count() == 1


@pytest.mark.django_db
def test_escalation_command_rejects_when_no_further_steps(due_occurrence, workflow_definition):
    execution = start_due_execution(due_occurrence, workflow_definition)
    advance_escalation(execution_id=execution.id)
    with pytest.raises(EscalationNotAllowedError):
        advance_escalation(execution_id=execution.id)


@pytest.mark.django_db
def test_exhausted_path_becomes_missed(due_occurrence):
    definition = _base_definition(retry={"max_retries": 0, "action": {"type": "SHOW_REMINDER"}}, escalation_steps=[])
    wf = create_workflow_definition(code="wf-missed", name="Missed WF", definition=definition)
    execution = start_execution(occurrence_id=due_occurrence.id, workflow_definition_id=wf.id)
    execution.active_until = timezone.now() - timedelta(seconds=1)
    execution.save(update_fields=["active_until"])
    process_timed_out_execution(execution)
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.MISSED
    assert EventRecord.objects.filter(event_type="ExecutionMissed").count() == 1


@pytest.mark.django_db
def test_cancel_execution(due_occurrence, workflow_definition):
    execution = start_due_execution(due_occurrence, workflow_definition)
    cancelled = cancel_execution(execution_id=execution.id)
    assert cancelled.status == ExecutionStatus.CANCELLED
    assert EventRecord.objects.filter(event_type="ExecutionCancelled").count() == 1


@pytest.mark.django_db
def test_action_result_idempotency(due_occurrence, workflow_definition):
    execution = start_due_execution(due_occurrence, workflow_definition)
    first = report_action_result(
        execution_id=execution.id,
        action_reference="action-1",
        action_type="SHOW_REMINDER",
        result_status="SUCCEEDED",
    )
    second = report_action_result(
        execution_id=execution.id,
        action_reference="action-1",
        action_type="SHOW_REMINDER",
        result_status="SUCCEEDED",
    )
    assert first.id == second.id
    assert ActionResult.objects.count() == 1


@pytest.mark.django_db
def test_action_success_does_not_auto_confirm(due_occurrence, workflow_definition):
    execution = start_due_execution(due_occurrence, workflow_definition)
    report_action_result(
        execution_id=execution.id,
        action_reference="action-2",
        action_type="SHOW_REMINDER",
        result_status="SUCCEEDED",
    )
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.ACTIVE
    assert not EventRecord.objects.filter(event_type="ExecutionConfirmed").exists()
    assert not EventRecord.objects.filter(event_type="MedicationTaken").exists()


@pytest.mark.django_db
def test_postpone_does_not_modify_scheduling(due_occurrence, workflow_definition):
    schedule_id = due_occurrence.schedule_definition_id
    before_count = Occurrence.objects.filter(schedule_definition_id=schedule_id).count()
    execution = start_due_execution(due_occurrence, workflow_definition)
    postpone_execution(execution_id=execution.id)
    after_count = Occurrence.objects.filter(schedule_definition_id=schedule_id).count()
    assert before_count == after_count


@pytest.mark.django_db
def test_communication_domain_is_registered():
    from django.apps import apps

    assert apps.is_installed("domains.communication")


@pytest.mark.django_db
def test_workflow_does_not_own_schedule_binding_model():
    from django.apps import apps

    assert not apps.is_installed("domains.workflow") or not hasattr(
        __import__("domains.workflow.models", fromlist=["models"]),
        "WorkflowScheduleBinding",
    )
