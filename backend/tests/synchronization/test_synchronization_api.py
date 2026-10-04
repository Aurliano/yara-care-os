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


@pytest.mark.django_db
def test_replica_idor_protection(api_client):
    from domains.device.models import DeviceModel
    from domains.device.services.devices import create_device
    from domains.device.services.assignments import assign_device
    from domains.identity_access.services.profiles import create_elder, create_user
    from domains.synchronization.services.replicas import get_replica_state

    model, _ = DeviceModel.objects.get_or_create(
        model_code="YARA-HUB-V1",
        defaults={
            "manufacturer": "Yara",
            "model_name": "Yara Hub",
            "device_type": "HUB",
        },
    )
    from domains.licensing.services.licenses import activate_license

    user_a = create_user(phone="+989127777771", password="pass", full_name="User A")
    elder_a = create_elder(actor=user_a, full_name="Elder A")
    activate_license(elder_id=elder_a.id, plan_code="BASIC")
    device_a = create_device(serial_number="SYNC-DEV-A", device_model_id=model.id)
    assign_device(device_id=device_a.id, elder_id=elder_a.id, assignment_type="OWNED")

    from domains.synchronization.services.replicas import get_or_create_replica_state

    get_or_create_replica_state(replica_identifier=device_a.id, replica_type="HUB")

    user_b = create_user(phone="+989127777772", password="pass", full_name="User B")
    api_client.force_authenticate(user=user_b)

    res_get = api_client.get(f"/api/v1/synchronization/replicas/{device_a.id}/")
    assert res_get.status_code == 403

    res_reset = api_client.post(f"/api/v1/synchronization/replicas/{device_a.id}/reset/")
    assert res_reset.status_code == 403

    api_client.force_authenticate(user=user_a)
    res_owner = api_client.get(f"/api/v1/synchronization/replicas/{device_a.id}/")
    assert res_owner.status_code == 200

