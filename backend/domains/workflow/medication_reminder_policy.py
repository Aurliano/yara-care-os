"""Canonical medication reminder timings for WorkflowDefinition JSON.

These numbers live in one place so seed data, the lab migrate command, and
tests cannot drift. The Workflow engine already owns timeout / retry /
escalation; this module only supplies the default policy.

Timeline from the first reminder:

- +0   SHOW_REMINDER
- +15m retry 1 (SHOW_REMINDER)
- +30m retry 2 (SHOW_REMINDER)
- +45m NOTIFY_CAREGIVER (soft caregiver alert)
- +60m MISSED, then INITIATE_CALL from the MedicationMissed handler
"""

from __future__ import annotations

from typing import Any

from domains.workflow.definition_schema import validate_workflow_definition

STEP_TIMEOUT_SECONDS = 900
RETRY_MAX = 2
RETRY_TIMEOUT_SECONDS = 900
NOTIFY_TIMEOUT_SECONDS = 900
POSTPONE_MAX_COUNT = 2
POSTPONE_DELAY_SECONDS = 300


def medication_reminder_definition() -> dict[str, Any]:
    definition = {
        "initial_action": {"type": "SHOW_REMINDER"},
        "confirmation_policy": {"accepted_evidence_types": ["HUB_CONFIRMATION"]},
        "step_timeout_seconds": STEP_TIMEOUT_SECONDS,
        "retry": {
            "max_retries": RETRY_MAX,
            "action": {"type": "SHOW_REMINDER"},
            "timeout_seconds": RETRY_TIMEOUT_SECONDS,
        },
        "postpone": {
            "allowed": True,
            "max_count": POSTPONE_MAX_COUNT,
            "delay_seconds": POSTPONE_DELAY_SECONDS,
        },
        "escalation_steps": [
            {"action": {"type": "NOTIFY_CAREGIVER"}, "timeout_seconds": NOTIFY_TIMEOUT_SECONDS},
        ],
    }
    validate_workflow_definition(definition)
    return definition


def definition_matches_medication_policy(definition: dict[str, Any] | None) -> bool:
    return definition == medication_reminder_definition()
