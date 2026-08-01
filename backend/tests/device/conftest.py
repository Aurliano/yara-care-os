import uuid

import pytest
from django.core.management import call_command

from domains.device.enums import DeviceCapabilityCode
from domains.device.services.device_models import register_device_model
from domains.device.services.devices import create_device
from domains.identity_access.services.profiles import create_elder, create_user
from domains.licensing.services.licenses import activate_license
from rest_framework.test import APIClient


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("migrate", verbosity=0)
        call_command("seed_identity_access", verbosity=0)
        call_command("seed_licensing", verbosity=0)


@pytest.fixture
def device_user(db):
    return create_user(
        phone="+989133333333",
        password="securepass123",
        full_name="Device Tester",
    )


@pytest.fixture
def elder(db, device_user):
    return create_elder(actor=device_user, full_name="Device Elder")


@pytest.fixture
def care_user(device_user):
    return device_user


@pytest.fixture
def licensed_elder(elder):
    activate_license(elder_id=elder.id, plan_code="BASIC")
    return elder


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def authenticated_client(api_client: APIClient, device_user) -> APIClient:
    api_client.force_authenticate(user=device_user)
    return api_client


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
def pillbox_model(db):
    return register_device_model(
        manufacturer="Yara",
        model_code=f"PB-{uuid.uuid4().hex[:6]}",
        model_name="PillBox One",
        capability_codes=[DeviceCapabilityCode.BLE, DeviceCapabilityCode.BATTERY],
        device_type="PILLBOX",
    )


@pytest.fixture
def hub_device(hub_model):
    return create_device(
        device_model_id=hub_model.id,
        serial_number=f"HUB-{uuid.uuid4().hex[:8]}",
        current_state={"battery_percent": 100, "network": "online"},
    )


@pytest.fixture
def peripheral_device(pillbox_model):
    return create_device(
        device_model_id=pillbox_model.id,
        serial_number=f"PB-{uuid.uuid4().hex[:8]}",
    )
