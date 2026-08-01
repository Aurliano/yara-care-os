"""Device domain models."""

from __future__ import annotations

import uuid

from django.db import models

from domains.device.enums import (
    AssignmentStatus,
    AssignmentType,
    CapabilityOverrideState,
    CommandStatus,
    CommandType,
    CompartmentAssignmentStatus,
    CompartmentStatus,
    DeviceModelStatus,
    DeviceOperationalStatus,
    PairingStatus,
)


class DeviceCapability(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=64)

    class Meta:
        db_table = "device_capability"

    def __str__(self) -> str:
        return self.code


class DeviceModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    manufacturer = models.CharField(max_length=128)
    model_code = models.CharField(max_length=64, unique=True)
    model_name = models.CharField(max_length=128)
    device_type = models.CharField(max_length=64, default="GENERIC")
    status = models.CharField(
        max_length=16,
        choices=DeviceModelStatus.choices,
        default=DeviceModelStatus.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "device_model"

    def __str__(self) -> str:
        return f"{self.manufacturer}:{self.model_code}"


class DeviceModelCapability(models.Model):
    device_model = models.ForeignKey(
        DeviceModel,
        on_delete=models.CASCADE,
        related_name="model_capabilities",
    )
    capability = models.ForeignKey(
        DeviceCapability,
        on_delete=models.PROTECT,
        related_name="model_capabilities",
    )

    class Meta:
        db_table = "device_model_capability"
        constraints = [
            models.UniqueConstraint(
                fields=["device_model", "capability"],
                name="device_model_capability_unique",
            ),
        ]


class Device(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device_model = models.ForeignKey(
        DeviceModel,
        on_delete=models.PROTECT,
        related_name="devices",
    )
    serial_number = models.CharField(max_length=128, unique=True)
    operational_status = models.CharField(
        max_length=16,
        choices=DeviceOperationalStatus.choices,
        default=DeviceOperationalStatus.INVENTORY,
    )
    current_state = models.JSONField(default=dict)
    configuration = models.JSONField(default=dict)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    aggregate_version = models.PositiveBigIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "device"
        indexes = [
            models.Index(fields=["operational_status"], name="device_operational_status_idx"),
        ]

    def __str__(self) -> str:
        return self.serial_number


class DeviceCapabilityOverride(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name="capability_overrides",
    )
    capability = models.ForeignKey(
        DeviceCapability,
        on_delete=models.PROTECT,
        related_name="device_overrides",
    )
    state = models.CharField(max_length=16, choices=CapabilityOverrideState.choices)
    reason = models.TextField()
    changed_by_user_id = models.UUIDField()
    effective_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "device_capability_override"
        indexes = [
            models.Index(
                fields=["device", "capability", "effective_at"],
                name="device_cap_override_idx",
            ),
        ]


class DeviceAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(
        Device,
        on_delete=models.PROTECT,
        related_name="assignments",
    )
    elder = models.ForeignKey(
        "identity_access.Elder",
        on_delete=models.PROTECT,
        related_name="device_assignments",
    )
    assignment_type = models.CharField(max_length=16, choices=AssignmentType.choices)
    status = models.CharField(max_length=16, choices=AssignmentStatus.choices)
    assigned_at = models.DateTimeField()
    unassigned_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "device_assignment"
        indexes = [
            models.Index(fields=["device", "status"], name="device_assignment_status_idx"),
            models.Index(fields=["elder", "status"], name="device_assignment_elder_idx"),
        ]


class Pairing(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hub_device = models.ForeignKey(
        Device,
        on_delete=models.PROTECT,
        related_name="hub_pairings",
    )
    peripheral_device = models.ForeignKey(
        Device,
        on_delete=models.PROTECT,
        related_name="peripheral_pairings",
    )
    status = models.CharField(
        max_length=16,
        choices=PairingStatus.choices,
        default=PairingStatus.PAIRING,
    )
    paired_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "device_pairing"
        indexes = [
            models.Index(fields=["hub_device", "status"], name="device_pairing_hub_idx"),
        ]


class Compartment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name="compartments",
    )
    number = models.PositiveIntegerField()
    label = models.CharField(max_length=64, blank=True, default="")
    status = models.CharField(
        max_length=16,
        choices=CompartmentStatus.choices,
        default=CompartmentStatus.ACTIVE,
    )

    class Meta:
        db_table = "device_compartment"
        constraints = [
            models.UniqueConstraint(
                fields=["device", "number"],
                name="device_compartment_unique_number",
            ),
        ]


class CompartmentAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    compartment = models.ForeignKey(
        Compartment,
        on_delete=models.PROTECT,
        related_name="assignments",
    )
    care_activity_reference = models.UUIDField()
    status = models.CharField(
        max_length=16,
        choices=CompartmentAssignmentStatus.choices,
        default=CompartmentAssignmentStatus.ACTIVE,
    )
    assigned_at = models.DateTimeField()
    unassigned_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "device_compartment_assignment"
        indexes = [
            models.Index(fields=["compartment", "status"], name="device_comp_assign_status_idx"),
        ]


class DeviceCommand(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    target_device = models.ForeignKey(
        Device,
        on_delete=models.PROTECT,
        related_name="commands",
    )
    command_type = models.CharField(max_length=32, choices=CommandType.choices)
    parameters = models.JSONField(default=dict)
    status = models.CharField(
        max_length=16,
        choices=CommandStatus.choices,
        default=CommandStatus.QUEUED,
    )
    expires_at = models.DateTimeField()
    result = models.JSONField(default=dict)
    failure_reason = models.CharField(max_length=255, blank=True, default="")
    idempotency_key = models.CharField(max_length=255, unique=True)
    execution_reference = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    executing_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "device_command"
        indexes = [
            models.Index(fields=["target_device", "status"], name="device_command_status_idx"),
            models.Index(fields=["execution_reference"], name="device_command_exec_ref_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.id}:{self.status}"
