"""Scheduling API serializers."""

from rest_framework import serializers

from domains.scheduling.models import Occurrence, ScheduleDefinition, ScheduleException


class ScheduleDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleDefinition
        fields = [
            "id",
            "owner_reference",
            "recurrence_definition",
            "timezone",
            "start_at",
            "end_at",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]


class ScheduleCreateSerializer(serializers.Serializer):
    owner_reference = serializers.CharField(max_length=255)
    recurrence_definition = serializers.JSONField()
    timezone = serializers.CharField(max_length=64)
    start_at = serializers.DateTimeField()
    end_at = serializers.DateTimeField(required=False, allow_null=True)


class ScheduleUpdateSerializer(serializers.Serializer):
    recurrence_definition = serializers.JSONField(required=False)
    timezone = serializers.CharField(max_length=64, required=False)
    start_at = serializers.DateTimeField(required=False)
    end_at = serializers.DateTimeField(required=False, allow_null=True)


class ScheduleExceptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleException
        fields = [
            "id",
            "schedule_definition",
            "original_time",
            "replacement_time",
            "exception_type",
            "reason",
        ]
        read_only_fields = fields


class ScheduleExceptionCreateSerializer(serializers.Serializer):
    original_time = serializers.DateTimeField()
    exception_type = serializers.CharField(max_length=16)
    replacement_time = serializers.DateTimeField(required=False, allow_null=True)
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")


class OccurrenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Occurrence
        fields = ["id", "schedule_definition", "scheduled_for", "status", "created_at"]
        read_only_fields = fields
