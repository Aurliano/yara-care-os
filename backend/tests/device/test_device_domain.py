import uuid
from datetime import timedelta

import pytest
from django.apps import apps
from django.utils import timezone

from domains.device.enums import (
    AssignmentStatus,
    AssignmentType,
    CapabilityOverrideState,
    CommandStatus,
    CommandType,
    CompartmentAssignmentStatus,
    DeviceCapabilityCode,
    PairingStatus,
)
from domains.device.exceptions import (
    CapabilityNotFoundError,
    CompartmentAssignmentError,
    EntitlementDeniedError,
    InvalidCapabilityOverrideError,
    InvalidCommandStateError,
)
from domains.device.models import DeviceCapabilityOverride, DeviceCommand
from domains.device.services.assignments import assign_device, get_assignments, return_device
from domains.device.services.commands import (
    cancel_command,
    complete_command,
    create_device_command,
    deliver_command,
    expire_command,
    fail_command,
    start_command_execution,
)
from domains.device.services.compartments import assign_compartment, create_compartment, release_compartment_assignment
from domains.device.services.devices import add_capability_override, get_effective_capability_state, update_device_state
from domains.device.services.pairing import activate_pairing, create_pairing, revoke_pairing
from domains.event.models import EventRecord


@pytest.mark.django_db
def test_device_model_capabilities_not_duplicated_on_device(hub_model, hub_device):
    assert hub_device.device_model_id == hub_model.id
    assert DeviceCapabilityCode.BLE in hub_model.model_capabilities.values_list("capability__code", flat=True)
    assert not hasattr(hub_device, "capabilities")


@pytest.mark.django_db
def test_device_aggregate_version_owned_by_device(hub_device):
    assert hub_device.aggregate_version == 1
    updated = update_device_state(device_id=hub_device.id, current_state={"online": True}, is_online=True)
    assert updated.aggregate_version == 2


@pytest.mark.django_db
def test_capability_override_requires_model_capability(hub_device, care_user):
    with pytest.raises(CapabilityNotFoundError):
        add_capability_override(
            device_id=hub_device.id,
            capability_code=DeviceCapabilityCode.CAMERA,
            state=CapabilityOverrideState.DISABLED,
            reason="missing capability",
            changed_by_user_id=care_user.id,
        )


@pytest.mark.django_db
def test_capability_override_requires_reason(hub_device, care_user):
    with pytest.raises(InvalidCapabilityOverrideError):
        add_capability_override(
            device_id=hub_device.id,
            capability_code=DeviceCapabilityCode.SPEAKER,
            state=CapabilityOverrideState.DISABLED,
            reason="   ",
            changed_by_user_id=care_user.id,
        )


@pytest.mark.django_db
def test_capability_override_is_auditable(hub_device, care_user):
    add_capability_override(
        device_id=hub_device.id,
        capability_code=DeviceCapabilityCode.SPEAKER,
        state=CapabilityOverrideState.DISABLED,
        reason="Speaker broken",
        changed_by_user_id=care_user.id,
    )
    assert DeviceCapabilityOverride.objects.filter(device=hub_device).count() == 1
    assert get_effective_capability_state(hub_device, DeviceCapabilityCode.SPEAKER) == CapabilityOverrideState.DISABLED


@pytest.mark.django_db
def test_assignment_history_preserved(hub_device, licensed_elder):
    assign_device(
        device_id=hub_device.id,
        elder_id=licensed_elder.id,
        assignment_type=AssignmentType.OWNED,
    )
    return_device(device_id=hub_device.id)
    history = get_assignments(device_id=hub_device.id)
    assert len(history) == 1
    assert history[0].status == AssignmentStatus.RETURNED
    assert history[0].unassigned_at is not None


@pytest.mark.django_db
def test_pairing_lifecycle(hub_device, peripheral_device):
    pairing = create_pairing(hub_device_id=hub_device.id, peripheral_device_id=peripheral_device.id)
    assert pairing.status == PairingStatus.PAIRING
    active = activate_pairing(pairing_id=pairing.id)
    assert active.status == PairingStatus.ACTIVE
    assert EventRecord.objects.filter(event_type="DevicePaired").count() == 1
    revoked = revoke_pairing(pairing_id=pairing.id)
    assert revoked.status == PairingStatus.REVOKED


@pytest.mark.django_db
def test_one_active_compartment_assignment(hub_device):
    compartment = create_compartment(device_id=hub_device.id, number=1, label="Morning")
    first = assign_compartment(compartment_id=compartment.id, care_activity_reference=uuid.uuid4())
    assert first.status == CompartmentAssignmentStatus.ACTIVE
    with pytest.raises(CompartmentAssignmentError):
        assign_compartment(compartment_id=compartment.id, care_activity_reference=uuid.uuid4())
    release_compartment_assignment(assignment_id=first.id)


@pytest.mark.django_db
def test_command_lifecycle(hub_device):
    expires = timezone.now() + timedelta(hours=1)
    command = create_device_command(
        target_device_id=hub_device.id,
        command_type=CommandType.OPEN_COMPARTMENT,
        idempotency_key="cmd-open-1",
        expires_at=expires,
        parameters={"compartment": 1},
    )
    assert command.status == CommandStatus.QUEUED
    delivered = deliver_command(command_id=command.id)
    assert delivered.status == CommandStatus.DELIVERED
    executing = start_command_execution(command_id=command.id)
    assert executing.status == CommandStatus.EXECUTING
    completed = complete_command(command_id=command.id, result={"opened": True})
    assert completed.status == CommandStatus.SUCCEEDED
    assert EventRecord.objects.filter(event_type="DeviceCommandCompleted").count() == 1


@pytest.mark.django_db
def test_terminal_command_is_immutable(hub_device):
    expires = timezone.now() + timedelta(hours=1)
    command = create_device_command(
        target_device_id=hub_device.id,
        command_type=CommandType.DIAGNOSTIC,
        idempotency_key="cmd-terminal-1",
        expires_at=expires,
    )
    deliver_command(command_id=command.id)
    start_command_execution(command_id=command.id)
    complete_command(command_id=command.id)
    again = deliver_command(command_id=command.id)
    assert again.status == CommandStatus.SUCCEEDED


@pytest.mark.django_db
def test_command_expiration(hub_device):
    expires = timezone.now() - timedelta(minutes=1)
    command = create_device_command(
        target_device_id=hub_device.id,
        command_type=CommandType.DIAGNOSTIC,
        idempotency_key="cmd-expired-1",
        expires_at=expires,
    )
    expired = expire_command(command_id=command.id)
    assert expired.status == CommandStatus.EXPIRED
    with pytest.raises(InvalidCommandStateError):
        start_command_execution(command_id=command.id)


@pytest.mark.django_db
def test_command_cancellation(hub_device):
    expires = timezone.now() + timedelta(hours=1)
    command = create_device_command(
        target_device_id=hub_device.id,
        command_type=CommandType.DIAGNOSTIC,
        idempotency_key="cmd-cancel-1",
        expires_at=expires,
    )
    cancelled = cancel_command(command_id=command.id)
    assert cancelled.status == CommandStatus.CANCELLED


@pytest.mark.django_db
def test_command_idempotency(hub_device):
    expires = timezone.now() + timedelta(hours=1)
    first = create_device_command(
        target_device_id=hub_device.id,
        command_type=CommandType.OPEN_COMPARTMENT,
        idempotency_key="cmd-idem-1",
        expires_at=expires,
    )
    second = create_device_command(
        target_device_id=hub_device.id,
        command_type=CommandType.OPEN_COMPARTMENT,
        idempotency_key="cmd-idem-1",
        expires_at=expires,
    )
    assert first.id == second.id
    assert DeviceCommand.objects.count() == 1


@pytest.mark.django_db
def test_repeated_delivery_does_not_reexecute(hub_device):
    expires = timezone.now() + timedelta(hours=1)
    command = create_device_command(
        target_device_id=hub_device.id,
        command_type=CommandType.OPEN_COMPARTMENT,
        idempotency_key="cmd-redeliver-1",
        expires_at=expires,
    )
    deliver_command(command_id=command.id)
    start_command_execution(command_id=command.id)
    complete_command(command_id=command.id, result={"opened": True})
    redelivered = deliver_command(command_id=command.id)
    assert redelivered.status == CommandStatus.SUCCEEDED
    assert EventRecord.objects.filter(event_type="DeviceCommandCompleted").count() == 1


@pytest.mark.django_db
def test_execution_reference_is_opaque_uuid_without_workflow_fk(hub_device):
    execution_ref = uuid.uuid4()
    expires = timezone.now() + timedelta(hours=1)
    command = create_device_command(
        target_device_id=hub_device.id,
        command_type=CommandType.OPEN_COMPARTMENT,
        idempotency_key="cmd-exec-ref-1",
        expires_at=expires,
        execution_reference=execution_ref,
    )
    assert command.execution_reference == execution_ref
    field = DeviceCommand._meta.get_field("execution_reference")
    assert field.__class__.__name__ == "UUIDField"


@pytest.mark.django_db
def test_multiple_commands_per_execution_reference(hub_device):
    execution_ref = uuid.uuid4()
    expires = timezone.now() + timedelta(hours=1)
    first = create_device_command(
        target_device_id=hub_device.id,
        command_type=CommandType.OPEN_COMPARTMENT,
        idempotency_key="cmd-multi-1",
        expires_at=expires,
        execution_reference=execution_ref,
    )
    second = create_device_command(
        target_device_id=hub_device.id,
        command_type=CommandType.CLOSE_COMPARTMENT,
        idempotency_key="cmd-multi-2",
        expires_at=expires,
        execution_reference=execution_ref,
    )
    assert first.id != second.id
    assert first.execution_reference == second.execution_reference


@pytest.mark.django_db
def test_device_publishes_hardware_facts_only(hub_device):
    update_device_state(
        device_id=hub_device.id,
        current_state={"battery_percent": 67, "network": "online"},
        is_online=True,
    )
    assert EventRecord.objects.filter(event_type="DeviceOnline").exists()
    forbidden = ["MedicationTaken", "ExecutionConfirmed", "ReminderCompleted"]
    for event_type in forbidden:
        assert not EventRecord.objects.filter(event_type=event_type, producer="device").exists()


@pytest.mark.django_db
def test_offline_first_current_state_only(hub_device):
    update_device_state(
        device_id=hub_device.id,
        current_state={"battery_percent": 55, "connectivity": "wifi"},
    )
    hub_device.refresh_from_db()
    assert "battery_percent" in hub_device.current_state
    assert hub_device.last_seen_at is not None


@pytest.mark.django_db
def test_no_monitoring_or_synchronization_domains():
    assert not apps.is_installed("domains.monitoring")
    assert apps.is_installed("domains.synchronization")


@pytest.mark.django_db
def test_assign_device_checks_licensing(hub_device, elder):
    with pytest.raises(EntitlementDeniedError):
        assign_device(
            device_id=hub_device.id,
            elder_id=elder.id,
            assignment_type=AssignmentType.OWNED,
        )


@pytest.mark.django_db
def test_fail_command_emits_hardware_event(hub_device):
    expires = timezone.now() + timedelta(hours=1)
    command = create_device_command(
        target_device_id=hub_device.id,
        command_type=CommandType.DIAGNOSTIC,
        idempotency_key="cmd-fail-1",
        expires_at=expires,
    )
    deliver_command(command_id=command.id)
    start_command_execution(command_id=command.id)
    failed = fail_command(command_id=command.id, failure_reason="motor fault")
    assert failed.status == CommandStatus.FAILED
    assert EventRecord.objects.filter(event_type="DeviceCommandFailed").count() == 1
