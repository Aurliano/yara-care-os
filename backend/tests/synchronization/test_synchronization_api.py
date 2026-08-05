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


import uuid

import pytest
from django.utils import timezone

from domains.synchronization.enums import OperationStatus, OperationType, SyncDirection
from domains.synchronization.identity import compute_payload_hash
from domains.synchronization.models import SynchronizationOperation
from domains.synchronization.services.sessions import start_synchronization
from domains.synchronization.enums import ReplicaType


@pytest.mark.django_db
def test_pending_operations_include_payload(authenticated_client, hub_replica_id):
    session = start_synchronization(
        replica_identifier=hub_replica_id,
        replica_type=ReplicaType.HUB,
        direction=SyncDirection.DOWNLOAD,
        idempotency_key="pending-payload-test",
    )
    aggregate_ref = uuid.uuid4()
    payload = {"workflow_execution_id": str(uuid.uuid4()), "status": "CONFIRMED", "aggregate_version": "2"}
    SynchronizationOperation.objects.create(
        synchronization_session=session,
        operation_type=OperationType.DELTA,
        aggregate_reference=aggregate_ref,
        aggregate_version="2",
        payload=payload,
        payload_type="workflow.execution.delta",
        payload_hash=compute_payload_hash(payload=payload),
        idempotency_key="pending-op-1",
        status=OperationStatus.PENDING,
        started_at=timezone.now(),
    )

    response = authenticated_client.get(
        f"/api/v1/synchronization/sessions/{session.id}/pending-operations/",
    )

    assert response.status_code == 200
    assert len(response.data) == 1
    operation = response.data[0]
    assert operation["payload"] == payload
    assert operation["payload_type"] == "workflow.execution.delta"
    assert operation["payload_hash"] == compute_payload_hash(payload=payload)
    assert operation["aggregate_reference"] == str(aggregate_ref)


@pytest.mark.django_db
def test_apply_endpoints_not_exposed(authenticated_client):
    response = authenticated_client.post("/api/v1/synchronization/sessions/apply-delta/", {}, format="json")
    assert response.status_code == 404
