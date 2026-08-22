"""Notification API serializers."""

from rest_framework import serializers

from domains.notification.models import CaregiverAlert


class CaregiverAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaregiverAlert
        fields = [
            "id",
            "title",
            "body",
            "severity",
            "occurred_at",
        ]
