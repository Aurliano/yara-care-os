"""Event API serializers."""

from rest_framework import serializers

from domains.event.models import EventRecord


class EventRecordSerializer(serializers.ModelSerializer):
    event_id = serializers.UUIDField(source="id", read_only=True)

    class Meta:
        model = EventRecord
        fields = [
            "event_id",
            "event_type",
            "event_version",
            "producer",
            "occurred_at",
            "recorded_at",
            "correlation_id",
            "causation_id",
            "payload",
        ]
        read_only_fields = fields
