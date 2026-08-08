"""Integration tests for hub provisioning API."""

import uuid

import pytest
from rest_framework.test import APIClient


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

