"""Medication reminder policy timings."""

from datetime import timedelta

import pytest
from django.utils import timezone

from domains.event.models import EventRecord
from domains.workflow.enums import ExecutionStatus
from domains.workflow.medication_reminder_policy import (
    NOTIFY_TIMEOUT_SECONDS,
    RETRY_MAX,
    RETRY_TIMEOUT_SECONDS,
    STEP_TIMEOUT_SECONDS,
    medication_reminder_definition,
)
from domains.workflow.services.executions import create_workflow_definition, start_execution
from domains.workflow.services.timeout import process_timed_out_execution


def test_medication_policy_numbers():
    definition = medication_reminder_definition()
    assert definition["step_timeout_seconds"] == 900
    assert definition["retry"]["max_retries"] == 2
    assert definition["retry"]["timeout_seconds"] == 900
    assert definition["escalation_steps"] == [
        {"action": {"type": "NOTIFY_CAREGIVER"}, "timeout_seconds": 900}
    ]
    assert STEP_TIMEOUT_SECONDS == RETRY_TIMEOUT_SECONDS == NOTIFY_TIMEOUT_SECONDS == 900
    assert RETRY_MAX == 2
    assert (
        STEP_TIMEOUT_SECONDS
        + RETRY_MAX * RETRY_TIMEOUT_SECONDS
        + NOTIFY_TIMEOUT_SECONDS
        == 3600
    )


@pytest.mark.django_db
def test_medication_policy_timeout_path(due_occurrence):
    workflow = create_workflow_definition(
        code="wf-med-policy",
        name="Medication Policy",
        definition=medication_reminder_definition(),
    )
    execution = start_execution(
        occurrence_id=due_occurrence.id,
        workflow_definition_id=workflow.id,
    )

    execution.active_until = timezone.now() - timedelta(seconds=1)
    execution.save(update_fields=["active_until"])
    process_timed_out_execution(execution)
    execution.refresh_from_db()
    assert execution.retry_count == 1
    assert execution.status == ExecutionStatus.ACTIVE
    assert execution.current_action["type"] == "SHOW_REMINDER"

    execution.active_until = timezone.now() - timedelta(seconds=1)
    execution.save(update_fields=["active_until"])
    process_timed_out_execution(execution)
    execution.refresh_from_db()
    assert execution.retry_count == 2
    assert execution.escalation_index == 0

    execution.active_until = timezone.now() - timedelta(seconds=1)
    execution.save(update_fields=["active_until"])
    process_timed_out_execution(execution)
    execution.refresh_from_db()
    assert execution.escalation_index == 1
    assert execution.current_action["type"] == "NOTIFY_CAREGIVER"
    assert EventRecord.objects.filter(event_type="EscalationTriggered").count() == 1

    execution.active_until = timezone.now() - timedelta(seconds=1)
    execution.save(update_fields=["active_until"])
    process_timed_out_execution(execution)
    execution.refresh_from_db()
    assert execution.status == ExecutionStatus.MISSED
    assert EventRecord.objects.filter(event_type="ExecutionMissed").count() == 1
