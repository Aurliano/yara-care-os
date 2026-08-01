"""Device API serializers."""

from rest_framework import serializers

from domains.device.models import (
    Compartment,
    CompartmentAssignment,
    Device,
    DeviceAssignment,
    DeviceCommand,
    DeviceModel,
    Pairing,
)


class DeviceModelSerializer(serializers.ModelSerializer):
    capabilities = serializers.SerializerMethodField()

    class Meta:
        model = DeviceModel
        fields = [
            "id",
            "manufacturer",
            "model_code",
            "model_name",
            "device_type",
            "status",
            "capabilities",
            "created_at",
        ]

    def get_capabilities(self, obj: DeviceModel) -> list[str]:
        return list(obj.model_capabilities.values_list("capability__code", flat=True))


class DeviceSerializer(serializers.ModelSerializer):
    device_model_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Device
        fields = [
            "id",
            "device_model_id",
            "serial_number",
            "operational_status",
            "current_state",
            "configuration",
            "last_seen_at",
            "aggregate_version",
            "created_at",
            "updated_at",
        ]


class DeviceCreateSerializer(serializers.Serializer):
    device_model_id = serializers.UUIDField()
    serial_number = serializers.CharField(max_length=128)
    configuration = serializers.DictField(required=False)
    current_state = serializers.DictField(required=False)


class DeviceAssignmentSerializer(serializers.ModelSerializer):
    device_id = serializers.UUIDField(read_only=True)
    elder_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = DeviceAssignment
        fields = [
            "id",
            "device_id",
            "elder_id",
            "assignment_type",
            "status",
            "assigned_at",
            "unassigned_at",
            "created_at",
        ]


class AssignDeviceSerializer(serializers.Serializer):
    elder_id = serializers.UUIDField()
    assignment_type = serializers.CharField(max_length=16)


class PairingSerializer(serializers.ModelSerializer):
    hub_device_id = serializers.UUIDField(read_only=True)
    peripheral_device_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Pairing
        fields = [
            "id",
            "hub_device_id",
            "peripheral_device_id",
            "status",
            "paired_at",
            "ended_at",
            "created_at",
            "updated_at",
        ]


class PairingCreateSerializer(serializers.Serializer):
    hub_device_id = serializers.UUIDField()
    peripheral_device_id = serializers.UUIDField()


class CompartmentSerializer(serializers.ModelSerializer):
    device_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Compartment
        fields = ["id", "device_id", "number", "label", "status"]


class CompartmentAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompartmentAssignment
        fields = [
            "id",
            "compartment_id",
            "care_activity_reference",
            "status",
            "assigned_at",
            "unassigned_at",
            "created_at",
        ]


class DeviceCommandSerializer(serializers.ModelSerializer):
    target_device_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = DeviceCommand
        fields = [
            "id",
            "target_device_id",
            "command_type",
            "parameters",
            "status",
            "expires_at",
            "result",
            "failure_reason",
            "idempotency_key",
            "execution_reference",
            "created_at",
            "delivered_at",
            "executing_at",
            "completed_at",
        ]


class DeviceCommandCreateSerializer(serializers.Serializer):
    target_device_id = serializers.UUIDField()
    command_type = serializers.CharField(max_length=32)
    idempotency_key = serializers.CharField(max_length=255)
    expires_at = serializers.DateTimeField()
    parameters = serializers.DictField(required=False)
    execution_reference = serializers.UUIDField(required=False, allow_null=True)


class DeviceCommandResultSerializer(serializers.Serializer):
    result = serializers.DictField(required=False)


class DeviceCommandFailSerializer(serializers.Serializer):
    failure_reason = serializers.CharField(max_length=255, required=False, allow_blank=True)
