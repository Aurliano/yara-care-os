"""Integration tests for hub provisioning API."""

import uuid

import pytest
from rest_framework.test import APIClient

from domains.device.enums import AssignmentStatus
from domains.device.models import DeviceAssignment
from domains.identity_access.services.profiles import create_elder, create_user
from domains.licensing.services.licenses import activate_license


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def provisioned_hub(hub_model, hub_device):
    return {
        "model_code": hub_model.model_code,
        "serial_number": hub_device.serial_number,
        "device_id": str(hub_device.id),
    }


def test_register_hub_device_creates_backend_assigned_identity(api_client, hub_model):
    serial = f"HUB-REG-{uuid.uuid4().hex[:8]}"
    response = api_client.post(
        "/api/v1/hub/provision/register/",
        {
            "serial_number": serial,
            "device_model_code": hub_model.model_code,
        },
        format="json",
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["device_id"]
    assert payload["replica_identifier"]
    assert payload["provisioning_state"] == "REGISTERED"
    assert payload["provisioned_at"]


def test_register_hub_device_is_idempotent(api_client, hub_model):
    serial = f"HUB-IDEM-{uuid.uuid4().hex[:8]}"
    first = api_client.post(
        "/api/v1/hub/provision/register/",
        {"serial_number": serial, "device_model_code": hub_model.model_code},
        format="json",
    ).json()
    second = api_client.post(
        "/api/v1/hub/provision/register/",
        {"serial_number": serial, "device_model_code": hub_model.model_code},
        format="json",
    ).json()
    assert first["device_id"] == second["device_id"]
    assert first["replica_identifier"] == second["replica_identifier"]


def test_authenticate_hub_device_returns_tokens(api_client, hub_model, integration_user):
    serial = f"HUB-AUTH-{uuid.uuid4().hex[:8]}"
    registered = api_client.post(
        "/api/v1/hub/provision/register/",
        {"serial_number": serial, "device_model_code": hub_model.model_code},
        format="json",
    ).json()
    response = api_client.post(
        "/api/v1/hub/provision/authenticate/",
        {
            "device_id": registered["device_id"],
            "phone": integration_user.phone,
            "password": "securepass123",
        },
        format="json",
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["access"]
    assert payload["refresh"]
    assert payload["provisioning_state"] == "READY"
    assert payload["replica_identifier"] == registered["replica_identifier"]
    from domains.device.models import Device

    device = Device.objects.get(pk=registered["device_id"])
    assert device.current_state.get("network") == "online"
    assert device.last_seen_at is not None


def test_provisioning_status_reflects_backend_state(api_client, hub_model, integration_user):
    serial = f"HUB-STATUS-{uuid.uuid4().hex[:8]}"
    registered = api_client.post(
        "/api/v1/hub/provision/register/",
        {"serial_number": serial, "device_model_code": hub_model.model_code},
        format="json",
    ).json()
    status_before = api_client.get(
        "/api/v1/hub/provision/status/",
        {"device_id": registered["device_id"]},
    ).json()
    assert status_before["provisioning_state"] == "REGISTERED"

    api_client.post(
        "/api/v1/hub/provision/authenticate/",
        {
            "device_id": registered["device_id"],
            "phone": integration_user.phone,
            "password": "securepass123",
        },
        format="json",
    )
    status_after = api_client.get(
        "/api/v1/hub/provision/status/",
        {"device_id": registered["device_id"]},
    ).json()
    assert status_after["provisioning_state"] == "READY"


def test_revoke_provisioning_requires_authentication(api_client, provisioned_hub):
    response = api_client.post(
        "/api/v1/hub/provision/revoke/",
        {"device_id": provisioned_hub["device_id"]},
        format="json",
    )
    assert response.status_code == 401


def test_reregister_after_ready_returns_same_identity(api_client, hub_model, integration_user):
    serial = f"HUB-READY-{uuid.uuid4().hex[:8]}"
    registered = api_client.post(
        "/api/v1/hub/provision/register/",
        {"serial_number": serial, "device_model_code": hub_model.model_code},
        format="json",
    ).json()
    api_client.post(
        "/api/v1/hub/provision/authenticate/",
        {
            "device_id": registered["device_id"],
            "phone": integration_user.phone,
            "password": "securepass123",
        },
        format="json",
    )
    reregistered = api_client.post(
        "/api/v1/hub/provision/register/",
        {"serial_number": serial, "device_model_code": hub_model.model_code},
        format="json",
    ).json()
    assert reregistered["device_id"] == registered["device_id"]
    assert reregistered["replica_identifier"] == registered["replica_identifier"]
    assert reregistered["provisioning_state"] == "READY"


def test_reregister_after_revoke_issues_new_replica(api_client, hub_model, integration_user):
    serial = f"HUB-REVOKE-{uuid.uuid4().hex[:8]}"
    registered = api_client.post(
        "/api/v1/hub/provision/register/",
        {"serial_number": serial, "device_model_code": hub_model.model_code},
        format="json",
    ).json()
    api_client.post(
        "/api/v1/hub/provision/authenticate/",
        {
            "device_id": registered["device_id"],
            "phone": integration_user.phone,
            "password": "securepass123",
        },
        format="json",
    )
    token = api_client.post(
        "/api/v1/auth/token/",
        {"phone": integration_user.phone, "password": "securepass123"},
        format="json",
    ).json()["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    api_client.post(
        "/api/v1/hub/provision/revoke/",
        {"device_id": registered["device_id"]},
        format="json",
    )
    api_client.credentials()
    reregistered = api_client.post(
        "/api/v1/hub/provision/register/",
        {"serial_number": serial, "device_model_code": hub_model.model_code},
        format="json",
    ).json()
    assert reregistered["device_id"] == registered["device_id"]
    assert reregistered["replica_identifier"] != registered["replica_identifier"]
    assert reregistered["provisioning_state"] == "REGISTERED"


def test_authenticate_reassigns_hub_to_authenticating_caregiver_elder(
    api_client,
    hub_model,
    integration_user,
    licensed_elder,
):
    serial = f"HUB-REBIND-{uuid.uuid4().hex[:8]}"
    registered = api_client.post(
        "/api/v1/hub/provision/register/",
        {"serial_number": serial, "device_model_code": hub_model.model_code},
        format="json",
    ).json()
    first = api_client.post(
        "/api/v1/hub/provision/authenticate/",
        {
            "device_id": registered["device_id"],
            "phone": integration_user.phone,
            "password": "securepass123",
        },
        format="json",
    )
    assert first.status_code == 200
    assert first.json()["elder_id"] == str(licensed_elder.id)

    second_user = create_user(
        phone="+989128888888",
        password="familylab123",
        full_name="Family Lab Caregiver",
    )
    second_elder = create_elder(actor=second_user, full_name="Family Lab Elder")
    activate_license(elder_id=second_elder.id, plan_code="BASIC")

    rebound = api_client.post(
        "/api/v1/hub/provision/authenticate/",
        {
            "device_id": registered["device_id"],
            "phone": second_user.phone,
            "password": "familylab123",
        },
        format="json",
    )
    assert rebound.status_code == 200
    assert rebound.json()["elder_id"] == str(second_elder.id)

    assigned = DeviceAssignment.objects.filter(
        device_id=registered["device_id"],
        status=AssignmentStatus.ASSIGNED,
    )
    assert assigned.count() == 1
    assert assigned.get().elder_id == second_elder.id

    api_client.force_authenticate(user=second_user)
    devices = api_client.get(f"/api/v1/elders/{second_elder.id}/devices/")
    assert devices.status_code == 200
    assert len(devices.json()) == 1
    assert devices.json()[0]["id"] == registered["device_id"]

    api_client.force_authenticate(user=integration_user)
    previous = api_client.get(f"/api/v1/elders/{licensed_elder.id}/devices/")
    assert previous.status_code == 200
    assert previous.json() == []


def test_hub_confirmation_unknown_execution_returns_404(api_client, hub_model, integration_user):
    serial = f"HUB-CONF-{uuid.uuid4().hex[:8]}"
    registered = api_client.post(
        "/api/v1/hub/provision/register/",
        {"serial_number": serial, "device_model_code": hub_model.model_code},
        format="json",
    ).json()
    auth = api_client.post(
        "/api/v1/hub/provision/authenticate/",
        {
            "device_id": registered["device_id"],
            "phone": integration_user.phone,
            "password": "securepass123",
        },
        format="json",
    )
    assert auth.status_code == 200
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {auth.json()['access']}")
    response = api_client.post(
        "/api/v1/hub/confirmations/",
        {
            "workflow_execution_id": str(uuid.uuid4()),
            "interaction_reference": "stale-local-execution",
        },
        format="json",
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Workflow execution not found."

