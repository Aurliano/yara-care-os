"""Synchronization API serializers."""

from rest_framework import serializers

from domains.synchronization.models import (
    ReplicaState,
    ReplicaVersion,
    SynchronizationConflict,
    SynchronizationOperation,
    SynchronizationSession,
)


class ReplicaStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReplicaState
        fields = [
            "id",
            "replica_identifier",
            "replica_type",
            "health",
            "status",
            "checkpoint_sequence",
            "checkpoint_token",
            "last_successful_sync",
            "statistics",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class SynchronizationSessionSerializer(serializers.ModelSerializer):
    replica_identifier = serializers.UUIDField(source="replica_state.replica_identifier", read_only=True)

    class Meta:
        model = SynchronizationSession
        fields = [
            "id",
            "replica_identifier",
            "direction",
            "status",
            "started_at",
            "completed_at",
            "cancelled_at",
            "statistics",
            "synchronization_token",
            "retry_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class StartSynchronizationSerializer(serializers.Serializer):
    replica_identifier = serializers.UUIDField()
    replica_type = serializers.ChoiceField(choices=["BACKEND", "HUB"])
    direction = serializers.ChoiceField(choices=["UPLOAD", "DOWNLOAD"])
    idempotency_key = serializers.CharField(max_length=128, required=False, allow_blank=True)


class SubmitPayloadSerializer(serializers.Serializer):
    aggregate_reference = serializers.UUIDField()
    aggregate_version = serializers.CharField(max_length=64)
    payload = serializers.JSONField()
    payload_type = serializers.CharField(max_length=64)
    payload_hash = serializers.CharField(max_length=64)
    idempotency_key = serializers.CharField(max_length=128)
    expected_version = serializers.CharField(max_length=64, required=False, allow_blank=True)


class ResolveConflictSerializer(serializers.Serializer):
    resolution_payload = serializers.JSONField()


class SynchronizationOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SynchronizationOperation
        fields = [
            "id",
            "operation_type",
            "aggregate_reference",
            "aggregate_version",
            "payload_type",
            "payload_hash",
            "status",
            "failure_reason",
            "started_at",
            "applied_at",
        ]
        read_only_fields = fields


class SynchronizationConflictSerializer(serializers.ModelSerializer):
    class Meta:
        model = SynchronizationConflict
        fields = [
            "id",
            "aggregate_reference",
            "conflict_type",
            "status",
            "local_version",
            "remote_version",
            "detected_at",
            "resolved_at",
        ]
        read_only_fields = fields


class CheckpointSerializer(serializers.Serializer):
    replica_identifier = serializers.UUIDField()
    checkpoint_sequence = serializers.IntegerField()
    checkpoint_token = serializers.UUIDField(allow_null=True)


class StatisticsSerializer(serializers.Serializer):
    replica_identifier = serializers.UUIDField()
    statistics = serializers.JSONField()
    last_successful_sync = serializers.CharField(allow_null=True)
    checkpoint_sequence = serializers.IntegerField()
