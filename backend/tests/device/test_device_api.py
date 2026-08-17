import pytest
from django.utils import timezone
from datetime import timedelta

from domains.device.enums import AssignmentType, CommandType
from domains.device.services.assignments import assign_device
from domains.identity_access.services.profiles import create_user


@pytest.mark.django_db
def test_create_device_api(authenticated_client, hub_model):
    response = authenticated_client.post(
        "/api/v1/devices/",
        {
            "device_model_id": str(hub_model.id),
            "serial_number": "API-HUB-001",
            "current_state": {"battery_percent": 90},
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["serial_number"] == "API-HUB-001"


@pytest.mark.django_db
def test_create_command_api(authenticated_client, hub_device):
    response = authenticated_client.post(
        f"/api/v1/devices/{hub_device.id}/commands/",
        {
            "command_type": CommandType.OPEN_COMPARTMENT,
            "idempotency_key": "api-cmd-1",
            "expires_at": (timezone.now() + timedelta(hours=1)).isoformat(),
            "parameters": {"compartment": 1},
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["status"] == "QUEUED"


@pytest.mark.django_db
def test_elder_device_list_api(authenticated_client, licensed_elder, hub_device):
    assign_device(
        device_id=hub_device.id,
        elder_id=licensed_elder.id,
        assignment_type=AssignmentType.OWNED,
    )
    response = authenticated_client.get(f"/api/v1/elders/{licensed_elder.id}/devices/")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == str(hub_device.id)
    assert body[0]["kind"] == "HUB"
    assert body[0]["serial_number"] == hub_device.serial_number
    assert body[0]["connectivity"] == "online"
    assert body[0]["battery_percent"] == 100


@pytest.mark.django_db
def test_elder_device_list_requires_membership(api_client, licensed_elder, hub_device):
    assign_device(
        device_id=hub_device.id,
        elder_id=licensed_elder.id,
        assignment_type=AssignmentType.OWNED,
    )
    outsider = create_user(
        phone="+989199999999",
        password="securepass123",
        full_name="Outsider",
    )
    api_client.force_authenticate(user=outsider)
    response = api_client.get(f"/api/v1/elders/{licensed_elder.id}/devices/")
    assert response.status_code == 403
