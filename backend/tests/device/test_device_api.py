import pytest
from django.utils import timezone
from datetime import timedelta

from domains.device.enums import CommandType


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
