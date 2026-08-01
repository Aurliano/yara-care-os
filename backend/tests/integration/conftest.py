"""Integration test fixtures."""

import uuid
from datetime import datetime

import pytest
from django.core.management import call_command
from zoneinfo import ZoneInfo

from domains.device.enums import DeviceCapabilityCode
from domains.device.services.device_models import register_device_model
from domains.device.services.devices import create_device
from domains.identity_access.services.profiles import create_elder, create_user
from domains.licensing.services.licenses import activate_license
from domains.scheduling.enums import OccurrenceStatus
from domains.scheduling.models import Occurrence
from domains.scheduling.services.schedules import create_schedule
from domains.workflow.definition_schema import validate_workflow_definition
from domains.workflow.services.executions import create_workflow_definition


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("migrate", verbosity=0)
        call_command("seed_identity_access", verbosity=0)
        call_command("seed_licensing", verbosity=0)


@pytest.fixture
def integration_user(db):
    return create_user(
        phone="+989136666666",
        password="securepass123",
        full_name="Integration Tester",
    )


@pytest.fixture
def elder(db, integration_user):
    return create_elder(actor=integration_user, full_name="Integration Elder")


@pytest.fixture
def licensed_elder(elder):
    activate_license(elder_id=elder.id, plan_code="BASIC")
    return elder


@pytest.fixture
def hub_model(db):
    return register_device_model(
        manufacturer="Yara",
        model_code=f"HUB-{uuid.uuid4().hex[:6]}",
        model_name="Galaxy Tab S2 Hub",
        capability_codes=[
            DeviceCapabilityCode.DISPLAY,
            DeviceCapabilityCode.SPEAKER,
            DeviceCapabilityCode.BLE,
            DeviceCapabilityCode.BATTERY,
        ],
        device_type="HUB",
    )


@pytest.fixture
def hub_device(hub_model):
    return create_device(
        device_model_id=hub_model.id,
        serial_number=f"HUB-{uuid.uuid4().hex[:8]}",
        current_state={"battery_percent": 100, "network": "online"},
    )


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
        code=f"wf-integration-{uuid.uuid4().hex[:8]}",
        name="Integration Workflow",
        definition=_base_workflow_definition(),
    )


@pytest.fixture
def recurrence_definition():
    return {"type": "daily", "time": "08:00"}


@pytest.fixture
def schedule_start_at():
    return _aware(datetime(2026, 8, 1, 0, 0, tzinfo=ZoneInfo("UTC")))


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
