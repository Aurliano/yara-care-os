"""Idempotent apply of the medication reminder policy."""

import uuid

import pytest
from django.core.management import call_command

from domains.care.services.prescriptions import create_prescription
from domains.workflow.medication_reminder_policy import (
    definition_matches_medication_policy,
    medication_reminder_definition,
)
from domains.workflow.services.executions import create_workflow_definition, get_workflow_definition
from integration.services.hub_dev_seed import DEV_WORKFLOW_CODE, _base_workflow_definition


@pytest.mark.django_db
def test_apply_medication_reminder_policy_updates_existing_medication_definition(
    licensed_elder,
    recurrence_definition,
    schedule_start_at,
):
    stale = {
        "initial_action": {"type": "SHOW_REMINDER"},
        "confirmation_policy": {"accepted_evidence_types": ["HUB_CONFIRMATION"]},
        "step_timeout_seconds": 60,
        "retry": {"max_retries": 1, "action": {"type": "SHOW_REMINDER"}, "timeout_seconds": 60},
        "postpone": {"allowed": True, "max_count": 2, "delay_seconds": 300},
        "escalation_steps": [{"action": {"type": "NOTIFY_CAREGIVER"}, "timeout_seconds": 60}],
    }
    workflow = create_workflow_definition(
        code=f"wf-stale-med-{uuid.uuid4().hex[:8]}",
        name="Stale Medication",
        definition=stale,
    )
    create_prescription(
        elder_id=licensed_elder.id,
        workflow_definition_id=workflow.id,
        recurrence_definition=recurrence_definition,
        timezone_name="UTC",
        start_at=schedule_start_at,
        display_title="Stale pill",
        medication_reference="med-stale",
        dosage_information="1 tablet",
        elder_friendly_description="Take pill",
    )
    assert not definition_matches_medication_policy(workflow.definition)

    call_command("apply_medication_reminder_policy", verbosity=0)
    updated = get_workflow_definition(workflow.id)
    assert definition_matches_medication_policy(updated.definition)

    call_command("apply_medication_reminder_policy", verbosity=0)
    again = get_workflow_definition(workflow.id)
    assert again.definition == updated.definition
    assert again.updated_at == updated.updated_at


def test_hub_dev_seed_uses_medication_policy():
    assert definition_matches_medication_policy(_base_workflow_definition())
    assert DEV_WORKFLOW_CODE == "wf-hub-dev-medication"
    assert medication_reminder_definition()["step_timeout_seconds"] == 900
