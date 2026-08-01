import uuid

import pytest

from domains.synchronization.identity import compute_payload_hash
from domains.synchronization.services.conflicts import detect_version_conflict, resolve_conflict
from domains.synchronization.services.operations import apply_delta, submit_aggregate_delta, submit_aggregate_snapshot
from domains.synchronization.services.replicas import (
    advance_checkpoint,
    get_checkpoint,
    get_or_create_replica_state,
    reset_replica,
)
from domains.synchronization.services.sessions import (
    cancel_synchronization,
    resume_synchronization,
    start_synchronization,
)
from domains.synchronization.enums import (
    ConflictStatus,
    OperationStatus,
    ReplicaType,
    SessionStatus,
    SyncDirection,
)


@pytest.fixture
def aggregate_ref() -> uuid.UUID:
    return uuid.uuid4()


def _payload(version: str = "1") -> dict:
    return {"aggregate_version": version, "opaque": True}


def _submit_kwargs(session_id, aggregate_ref, version="1", key="delta-1"):
    payload = _payload(version)
    return {
        "session_id": session_id,
        "aggregate_reference": aggregate_ref,
        "aggregate_version": version,
        "payload": payload,
        "payload_type": "application/json",
        "payload_hash": compute_payload_hash(payload=payload),
        "idempotency_key": key,
    }


@pytest.mark.django_db
def test_session_lifecycle(hub_replica_id):
    session = start_synchronization(
        replica_identifier=hub_replica_id,
        replica_type=ReplicaType.HUB,
        direction=SyncDirection.UPLOAD,
        idempotency_key="start-1",
    )
    assert session.status == SessionStatus.SESSION_STARTED

    cancelled = cancel_synchronization(session_id=session.id)
    assert cancelled.status == SessionStatus.CANCELLED
    assert cancelled.cancelled_at is not None


@pytest.mark.django_db
def test_replica_lifecycle(hub_replica_id):
    replica = get_or_create_replica_state(
        replica_identifier=hub_replica_id,
        replica_type=ReplicaType.HUB,
    )
    assert replica.checkpoint_sequence == 0

    reset = reset_replica(replica_identifier=hub_replica_id)
    assert reset.status == "RESETTING"
    assert reset.checkpoint_sequence == 0


@pytest.mark.django_db
def test_checkpoint_monotonicity(hub_replica_id):
    get_or_create_replica_state(replica_identifier=hub_replica_id, replica_type=ReplicaType.HUB)
    advance_checkpoint(replica_identifier=hub_replica_id, checkpoint_token=uuid.uuid4())
    advance_checkpoint(replica_identifier=hub_replica_id, checkpoint_token=uuid.uuid4())

    checkpoint = get_checkpoint(replica_identifier=hub_replica_id)
    assert checkpoint["checkpoint_sequence"] == 2


@pytest.mark.django_db
def test_delta_validation_and_apply(hub_replica_id, aggregate_ref):
    session = start_synchronization(
        replica_identifier=hub_replica_id,
        replica_type=ReplicaType.HUB,
        direction=SyncDirection.UPLOAD,
    )
    operation = submit_aggregate_delta(**_submit_kwargs(session.id, aggregate_ref))
    assert operation.status == OperationStatus.APPLIED

    session.refresh_from_db()
    assert session.status == SessionStatus.SESSION_COMPLETED


@pytest.mark.django_db
def test_snapshot_validation_first_sync(hub_replica_id, aggregate_ref):
    session = start_synchronization(
        replica_identifier=hub_replica_id,
        replica_type=ReplicaType.HUB,
        direction=SyncDirection.DOWNLOAD,
    )
    kwargs = _submit_kwargs(session.id, aggregate_ref, key="snapshot-1")
    operation = submit_aggregate_snapshot(**kwargs)
    assert operation.status == OperationStatus.APPLIED


@pytest.mark.django_db
def test_version_mismatch_conflict(hub_replica_id, aggregate_ref):
    session = start_synchronization(
        replica_identifier=hub_replica_id,
        replica_type=ReplicaType.HUB,
        direction=SyncDirection.UPLOAD,
    )
    submit_aggregate_delta(**_submit_kwargs(session.id, aggregate_ref, version="1", key="v1"))

    session2 = start_synchronization(
        replica_identifier=hub_replica_id,
        replica_type=ReplicaType.HUB,
        direction=SyncDirection.UPLOAD,
        idempotency_key="start-2",
    )
    replica = session2.replica_state
    conflict = detect_version_conflict(
        replica=replica,
        session=session2,
        aggregate_reference=aggregate_ref,
        incoming_version="1",
        expected_version="2",
    )
    assert conflict is not None
    assert conflict.conflict_type == "VERSION_MISMATCH"


@pytest.mark.django_db
def test_resolve_conflict(hub_replica_id, aggregate_ref):
    session = start_synchronization(
        replica_identifier=hub_replica_id,
        replica_type=ReplicaType.HUB,
        direction=SyncDirection.UPLOAD,
    )
    conflict = detect_version_conflict(
        replica=session.replica_state,
        session=session,
        aggregate_reference=aggregate_ref,
        incoming_version="3",
        expected_version="5",
    )
    resolved = resolve_conflict(
        conflict_id=conflict.id,
        resolution_payload={"aggregate_version": "5", "opaque": True},
    )
    assert resolved.status == ConflictStatus.RESOLVED


@pytest.mark.django_db
def test_resume_synchronization(hub_replica_id):
    from domains.synchronization.services.sessions import mark_transfer_failed

    session = start_synchronization(
        replica_identifier=hub_replica_id,
        replica_type=ReplicaType.HUB,
        direction=SyncDirection.UPLOAD,
    )
    failed = mark_transfer_failed(session_id=session.id, reason="network")
    assert failed.status == SessionStatus.RETRY_SCHEDULED

    resumed = resume_synchronization(session_id=session.id)
    assert resumed.status == SessionStatus.SESSION_STARTED
    assert resumed.retry_count == 1


@pytest.mark.django_db
def test_idempotent_submit(hub_replica_id, aggregate_ref):
    session = start_synchronization(
        replica_identifier=hub_replica_id,
        replica_type=ReplicaType.HUB,
        direction=SyncDirection.UPLOAD,
    )
    kwargs = _submit_kwargs(session.id, aggregate_ref)
    first = submit_aggregate_delta(**kwargs)
    second = submit_aggregate_delta(**kwargs)
    assert first.id == second.id


@pytest.mark.django_db
def test_idempotent_apply(hub_replica_id, aggregate_ref):
    session = start_synchronization(
        replica_identifier=hub_replica_id,
        replica_type=ReplicaType.HUB,
        direction=SyncDirection.UPLOAD,
    )
    operation = submit_aggregate_delta(**_submit_kwargs(session.id, aggregate_ref, key="apply-once"))
    again = apply_delta(operation_id=operation.id)
    assert again.status == OperationStatus.APPLIED


@pytest.mark.django_db
def test_no_business_domain_imports():
    import importlib
    import pkgutil

    forbidden = (
        "domains.care",
        "domains.workflow",
        "domains.device",
        "domains.communication",
        "domains.scheduling",
        "domains.licensing",
        "domains.identity_access",
    )
    package = importlib.import_module("domains.synchronization")
    for _, module_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        if "test" in module_name or "migrations" in module_name:
            continue
        module = importlib.import_module(module_name)
        source = getattr(module, "__file__", "") or ""
        if not source.endswith(".py"):
            continue
        with open(source, encoding="utf-8") as handle:
            content = handle.read()
        for name in forbidden:
            assert name not in content, f"{module_name} references {name}"


@pytest.mark.django_db
def test_no_business_events_published(hub_replica_id, aggregate_ref):
    from domains.event.models import EventRecord

    session = start_synchronization(
        replica_identifier=hub_replica_id,
        replica_type=ReplicaType.HUB,
        direction=SyncDirection.UPLOAD,
    )
    submit_aggregate_delta(**_submit_kwargs(session.id, aggregate_ref, key="events-1"))

    forbidden_types = {
        "MedicationTaken",
        "ExecutionConfirmed",
        "ReminderCompleted",
        "DeviceCommandCompleted",
    }
    published = set(EventRecord.objects.values_list("event_type", flat=True))
    assert forbidden_types.isdisjoint(published)


@pytest.mark.django_db
def test_start_synchronization_idempotent(hub_replica_id):
    first = start_synchronization(
        replica_identifier=hub_replica_id,
        replica_type=ReplicaType.HUB,
        direction=SyncDirection.UPLOAD,
        idempotency_key="same-start",
    )
    second = start_synchronization(
        replica_identifier=hub_replica_id,
        replica_type=ReplicaType.HUB,
        direction=SyncDirection.UPLOAD,
        idempotency_key="same-start",
    )
    assert first.id == second.id
