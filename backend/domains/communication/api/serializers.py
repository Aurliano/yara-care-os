"""Communication API serializers."""

from rest_framework import serializers

from domains.communication.models import CallAttempt, CommunicationSession, Contact, SessionParticipant


class ContactSerializer(serializers.ModelSerializer):
    elder_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Contact
        fields = [
            "id",
            "elder_id",
            "display_name",
            "phone",
            "communication_identities",
            "preferred_channel",
            "photo_reference",
            "is_priority",
            "status",
            "archived_at",
            "created_at",
            "updated_at",
        ]


class ContactCreateSerializer(serializers.Serializer):
    display_name = serializers.CharField(max_length=128)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True, default="")
    communication_identities = serializers.ListField(child=serializers.DictField(), required=False)
    preferred_channel = serializers.CharField(max_length=16)
    photo_reference = serializers.UUIDField(required=False, allow_null=True)


class ContactUpdateSerializer(serializers.Serializer):
    display_name = serializers.CharField(max_length=128, required=False)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    communication_identities = serializers.ListField(child=serializers.DictField(), required=False)
    preferred_channel = serializers.CharField(max_length=16, required=False)
    photo_reference = serializers.UUIDField(required=False, allow_null=True)


class SessionParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionParticipant
        fields = ["id", "communication_session_id", "contact_id", "user_id", "role", "created_at"]


class CallAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallAttempt
        fields = [
            "id",
            "communication_session_id",
            "attempt_number",
            "outcome",
            "failure_reason",
            "started_at",
            "ended_at",
            "created_at",
        ]


class CommunicationSessionSerializer(serializers.ModelSerializer):
    elder_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = CommunicationSession
        fields = [
            "id",
            "elder_id",
            "channel",
            "status",
            "outcome",
            "initiated_at",
            "connected_at",
            "ended_at",
            "external_execution_reference",
            "created_at",
            "updated_at",
        ]


class InitiateSessionSerializer(serializers.Serializer):
    channel = serializers.CharField(max_length=16)
    initiator_contact_id = serializers.UUIDField(required=False, allow_null=True)
    initiator_user_id = serializers.UUIDField(required=False, allow_null=True)
    recipient_contact_id = serializers.UUIDField()
    external_execution_reference = serializers.UUIDField(required=False, allow_null=True)


class ReportAttemptResultSerializer(serializers.Serializer):
    outcome = serializers.CharField(max_length=16)
    failure_reason = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
