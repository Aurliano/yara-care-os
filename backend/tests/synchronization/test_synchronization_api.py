import uuid

import pytest

from domains.synchronization.identity import compute_payload_hash


@pytest.mark.django_db
def test_start_session_api(authenticated_client, hub_replica_id):
    response = authenticated_client.post(
        "/api/v1/synchronization/sessions/start/",
        {
            "replica_identifier": str(hub_replica_id),
            "replica_type": "HUB",
            "direction": "UPLOAD",
            "idempotency_key": "api-start-1",
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["status"] == "SESSION_STARTED"


@pytest.mark.django_db
def test_submit_delta_api(authenticated_client, hub_replica_id):
    start = authenticated_client.post(
        "/api/v1/synchronization/sessions/start/",
        {
            "replica_identifier": str(hub_replica_id),
            "replica_type": "HUB",
            "direction": "UPLOAD",
        },
        format="json",
    )
    session_id = start.data["id"]
    aggregate_ref = uuid.uuid4()
    payload = {"opaque": True, "aggregate_version": "1"}
    response = authenticated_client.post(
        f"/api/v1/synchronization/sessions/{session_id}/delta/",
        {
            "aggregate_reference": str(aggregate_ref),
            "aggregate_version": "1",
            "payload": payload,
            "payload_type": "application/json",
            "payload_hash": compute_payload_hash(payload=payload),
            "idempotency_key": "api-delta-1",
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["status"] == "APPLIED"


@pytest.mark.django_db
def test_get_pending_operations_api(authenticated_client, hub_replica_id):
    start = authenticated_client.post(
        "/api/v1/synchronization/sessions/start/",
        {
            "replica_identifier": str(hub_replica_id),
            "replica_type": "HUB",
            "direction": "UPLOAD",
        },
        format="json",
    )
    session_id = start.data["id"]
    response = authenticated_client.get(f"/api/v1/synchronization/sessions/{session_id}/pending-operations/")
    assert response.status_code == 200
    assert response.data == []


@pytest.mark.django_db
def test_apply_endpoints_not_exposed(authenticated_client):
    response = authenticated_client.post("/api/v1/synchronization/sessions/apply-delta/", {}, format="json")
    assert response.status_code == 404
