import uuid
from datetime import datetime, timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from zoneinfo import ZoneInfo

from domains.identity_access.services.profiles import create_user
from domains.scheduling.enums import OccurrenceStatus
from domains.scheduling.models import Occurrence
from domains.scheduling.services.schedules import create_schedule
from domains.workflow.definition_schema import validate_workflow_definition
from domains.workflow.services.executions import create_workflow_definition, start_execution


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def authenticated_client(api_client: APIClient, db) -> APIClient:
    user = create_user(
        phone="+989131111111",
        password="securepass123",
        full_name="Workflow Tester",
    )
    api_client.force_authenticate(user=user)
    return api_client


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt


def _base_definition(**overrides) -> dict:
    definition = {
        "initial_action": {"type": "SHOW_REMINDER"},
        "confirmation_policy": {"accepted_evidence_types": ["HUB_CONFIRMATION"]},
        "step_timeout_seconds": 60,
        "retry": {"max_retries": 1, "action": {"type": "SHOW_REMINDER"}, "timeout_seconds": 60},
        "postpone": {"allowed": True, "max_count": 2, "delay_seconds": 300},
        "escalation_steps": [{"action": {"type": "NOTIFY_CAREGIVER"}, "timeout_seconds": 60}],
    }
    definition.update(overrides)
    validate_workflow_definition(definition)
    return definition


@pytest.fixture
def workflow_definition(db):
    return create_workflow_definition(
        code=f"wf-{uuid.uuid4().hex[:8]}",
        name="Test Workflow",
        definition=_base_definition(),
    )


@pytest.fixture
def due_occurrence(workflow_definition):
    schedule = create_schedule(
        owner_reference="care_activity:test",
        recurrence_definition={"type": "daily", "time": "08:00"},
        timezone_name="UTC",
        start_at=_aware(datetime(2026, 7, 1, 0, 0, tzinfo=ZoneInfo("UTC"))),
    )
    occurrence = Occurrence.objects.filter(schedule_definition=schedule).first()
    occurrence.status = OccurrenceStatus.DUE
    occurrence.save(update_fields=["status"])
    return occurrence


def start_due_execution(occurrence, workflow_definition):
    return start_execution(
        occurrence_id=occurrence.id,
        workflow_definition_id=workflow_definition.id,
    )
