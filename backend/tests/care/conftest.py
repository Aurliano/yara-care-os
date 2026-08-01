import uuid
from datetime import datetime

import pytest
from django.core.management import call_command
from zoneinfo import ZoneInfo

from domains.identity_access.services.profiles import create_elder, create_user
from domains.workflow.definition_schema import validate_workflow_definition
from domains.workflow.services.executions import create_workflow_definition
from rest_framework.test import APIClient


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("migrate", verbosity=0)
        call_command("seed_identity_access", verbosity=0)


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


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
def authenticated_client(api_client: APIClient, care_user) -> APIClient:
    api_client.force_authenticate(user=care_user)
    return api_client


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt


def _base_workflow_definition(**overrides) -> dict:
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
        code=f"wf-care-{uuid.uuid4().hex[:8]}",
        name="Care Workflow",
        definition=_base_workflow_definition(),
    )


@pytest.fixture
def recurrence_definition():
    return {"type": "daily", "time": "08:00"}


@pytest.fixture
def schedule_start_at():
    return _aware(datetime(2026, 8, 1, 0, 0, tzinfo=ZoneInfo("UTC")))
