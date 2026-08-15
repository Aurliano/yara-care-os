"""Tests for hub incremental download staging."""

import uuid

import pytest
from rest_framework.test import APIClient

from domains.care.enums import CareActivityType
from domains.care.services.activities import create_care_activity
from domains.device.enums import AssignmentType
from domains.device.services.assignments import assign_device
from domains.synchronization.enums import OperationType
from domains.synchronization.models import ReplicaVersion
from domains.synchronization.services.replicas import get_replica_state
from integration.services.hub_download_staging import complete_hub_download_session, stage_hub_download_operations
from integration.runtime.adapters.synchronization import start_download_session
from integration.context import IntegrationContext


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_incremental_download_stages_care_delta_after_snapshot(
    api_client: APIClient,
    integration_user,
    licensed_elder,
    hub_model,
    hub_device,
    workflow_definition,
    recurrence_definition,
    schedule_start_at,
):
    api_client.force_authenticate(user=integration_user)

    register = api_client.post(
        "/api/v1/hub/provision/register/",
        {
            "serial_number": hub_device.serial_number,
            "device_model_code": hub_model.model_code,
        },
        format="json",
    )
    assert register.status_code == 201
    replica_id = uuid.UUID(register.json()["replica_identifier"])
    device_id = uuid.UUID(register.json()["device_id"])

    assign_device(
        device_id=device_id,
        elder_id=licensed_elder.id,
        assignment_type=AssignmentType.OWNED,
    )

    activity = create_care_activity(
        elder_id=licensed_elder.id,
        activity_type=CareActivityType.MEDICATION,
        workflow_definition_id=workflow_definition.id,
        recurrence_definition=recurrence_definition,
        timezone_name="UTC",
        start_at=schedule_start_at,
        display_title="Morning Medication",
    )

    auth = api_client.post(
        "/api/v1/hub/provision/authenticate/",
        {
            "device_id": str(device_id),
            "phone": integration_user.phone,
            "password": "securepass123",
        },
        format="json",
    )
    assert auth.status_code == 200

    ctx = IntegrationContext(
        device_id=device_id,
        replica_id=replica_id,
        correlation_id="test-correlation",
    )

    snapshot_session = start_download_session(ctx, idempotency_key="snapshot-session")
    assert stage_hub_download_operations(ctx=ctx, session=snapshot_session) == 1
    complete_hub_download_session(ctx=ctx, session_id=snapshot_session.id)

    replica = get_replica_state(replica_identifier=replica_id)
    assert replica.checkpoint_sequence == 1
    assert ReplicaVersion.objects.filter(replica_state=replica, aggregate_reference=activity.id).exists()

    activity.display_title = "Updated Morning Medication"
    activity.aggregate_version = activity.aggregate_version + 1
    activity.save(update_fields=["display_title", "aggregate_version", "updated_at"])

    delta_session = start_download_session(ctx, idempotency_key="delta-session")
    staged = stage_hub_download_operations(ctx=ctx, session=delta_session)
    assert staged == 1

    pending = api_client.get(
        f"/api/v1/synchronization/sessions/{delta_session.id}/pending-operations/",
    )
    assert pending.status_code == 200
    operations = pending.json()
    assert len(operations) == 1
    assert operations[0]["operation_type"] == OperationType.DELTA
    assert operations[0]["payload_type"] == "care.activity.delta"
    assert operations[0]["payload"]["display_title"] == "Updated Morning Medication"
    assert "schedule_definition" in operations[0]["payload"]
    assert len(operations[0]["payload"]["occurrences"]) >= 1


@pytest.mark.django_db
def test_incremental_download_stages_care_delta_after_schedule_time_change(
    api_client: APIClient,
    integration_user,
    licensed_elder,
    hub_model,
    hub_device,
    workflow_definition,
    recurrence_definition,
    schedule_start_at,
):
    from domains.care.services.activities import update_care_activity

    api_client.force_authenticate(user=integration_user)

    register = api_client.post(
        "/api/v1/hub/provision/register/",
        {
            "serial_number": hub_device.serial_number,
            "device_model_code": hub_model.model_code,
        },
        format="json",
    )
    assert register.status_code == 201
    replica_id = uuid.UUID(register.json()["replica_identifier"])
    device_id = uuid.UUID(register.json()["device_id"])

    assign_device(
        device_id=device_id,
        elder_id=licensed_elder.id,
        assignment_type=AssignmentType.OWNED,
    )

    activity = create_care_activity(
        elder_id=licensed_elder.id,
        activity_type=CareActivityType.MEDICATION,
        workflow_definition_id=workflow_definition.id,
        recurrence_definition=recurrence_definition,
        timezone_name="UTC",
        start_at=schedule_start_at,
        display_title="Morning Medication",
    )

    api_client.post(
        "/api/v1/hub/provision/authenticate/",
        {
            "device_id": str(device_id),
            "phone": integration_user.phone,
            "password": "securepass123",
        },
        format="json",
    )

    ctx = IntegrationContext(
        device_id=device_id,
        replica_id=replica_id,
        correlation_id="test-correlation",
    )

    snapshot_session = start_download_session(ctx, idempotency_key="snapshot-session-schedule")
    assert stage_hub_download_operations(ctx=ctx, session=snapshot_session) == 1
    complete_hub_download_session(ctx=ctx, session_id=snapshot_session.id)

    update_care_activity(
        activity.id,
        recurrence_definition={"type": "daily", "time": "09:30"},
        timezone_name="UTC",
    )

    delta_session = start_download_session(ctx, idempotency_key="delta-session-schedule")
    staged = stage_hub_download_operations(ctx=ctx, session=delta_session)
    assert staged == 1

    pending = api_client.get(
        f"/api/v1/synchronization/sessions/{delta_session.id}/pending-operations/",
    )
    assert pending.status_code == 200
    operations = pending.json()
    assert len(operations) == 1
    assert operations[0]["operation_type"] == OperationType.DELTA
    assert operations[0]["payload_type"] == "care.activity.delta"
    assert '"time": "09:30"' in operations[0]["payload"]["schedule_definition"]["recurrence_definition_json"]
    assert len(operations[0]["payload"]["occurrences"]) >= 1


@pytest.mark.django_db
def test_incremental_download_returns_no_changes_when_versions_match(
    api_client: APIClient,
    integration_user,
    licensed_elder,
    hub_model,
    hub_device,
    workflow_definition,
    recurrence_definition,
    schedule_start_at,
):
    api_client.force_authenticate(user=integration_user)

    register = api_client.post(
        "/api/v1/hub/provision/register/",
        {
            "serial_number": hub_device.serial_number,
            "device_model_code": hub_model.model_code,
        },
        format="json",
    )
    replica_id = uuid.UUID(register.json()["replica_identifier"])
    device_id = uuid.UUID(register.json()["device_id"])
    assign_device(
        device_id=device_id,
        elder_id=licensed_elder.id,
        assignment_type=AssignmentType.OWNED,
    )

    create_care_activity(
        elder_id=licensed_elder.id,
        activity_type=CareActivityType.MEDICATION,
        workflow_definition_id=workflow_definition.id,
        recurrence_definition=recurrence_definition,
        timezone_name="UTC",
        start_at=schedule_start_at,
        display_title="Stable Medication",
    )

    api_client.post(
        "/api/v1/hub/provision/authenticate/",
        {
            "device_id": str(device_id),
            "phone": integration_user.phone,
            "password": "securepass123",
        },
        format="json",
    )

    ctx = IntegrationContext(
        device_id=device_id,
        replica_id=replica_id,
        correlation_id="test-correlation",
    )

    snapshot_session = start_download_session(ctx, idempotency_key="snapshot-session-2")
    stage_hub_download_operations(ctx=ctx, session=snapshot_session)
    complete_hub_download_session(ctx=ctx, session_id=snapshot_session.id)

    delta_session = start_download_session(ctx, idempotency_key="delta-session-2")
    assert stage_hub_download_operations(ctx=ctx, session=delta_session) == 0
