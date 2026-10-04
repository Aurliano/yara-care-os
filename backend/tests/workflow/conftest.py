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
def workflow_user(db):
    return create_user(
        phone="+989131111111",
        password="securepass123",
        full_name="Workflow Tester",
    )


@pytest.fixture
def workflow_elder(workflow_user):
    from domains.identity_access.services.profiles import create_elder

    return create_elder(actor=workflow_user, full_name="Workflow Elder")


@pytest.fixture
def authenticated_client(api_client: APIClient, workflow_user) -> APIClient:
    api_client.force_authenticate(user=workflow_user)
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
def due_occurrence(workflow_definition, workflow_elder):
    from domains.care.enums import CareActivityType
    from domains.care.services.activities import create_care_activity

    now = timezone.now().replace(microsecond=0)
    activity = create_care_activity(
        elder_id=workflow_elder.id,
        activity_type=CareActivityType.MEDICATION,
        workflow_definition_id=workflow_definition.id,
        recurrence_definition={"type": "daily", "times": [now.strftime("%H:%M")]},
        timezone_name="UTC",
        start_at=now - timedelta(minutes=10),
        display_title="Test Workflow Medication",
    )
    occurrence = Occurrence.objects.filter(schedule_definition_id=activity.schedule_definition_id).first()
    if occurrence is None:
        occurrence = Occurrence.objects.create(
            id=uuid.uuid4(),
            schedule_definition_id=activity.schedule_definition_id,
            scheduled_for=now,
            status=OccurrenceStatus.DUE,
        )
    else:
        occurrence.status = OccurrenceStatus.DUE
        occurrence.save(update_fields=["status"])
    return occurrence



def start_due_execution(occurrence, workflow_definition):
    return start_execution(
        occurrence_id=occurrence.id,
        workflow_definition_id=workflow_definition.id,
    )
