"""Identity & Access API serializers."""

from django.utils import timezone
from rest_framework import serializers

from domains.identity_access.models import (
    Elder,
    EmergencyRecipient,
    Invitation,
    Membership,
    User,
)


class RegisterSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField(required=False, allow_blank=True, default="")


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone", "email", "full_name", "status", "created_at"]
        read_only_fields = fields


class UserProfileUpdateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255, required=False)
    email = serializers.EmailField(required=False, allow_blank=True)


class ElderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Elder
        fields = ["id", "full_name", "birth_date", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "status", "created_at", "updated_at"]


class ElderCreateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    birth_date = serializers.DateField(required=False, allow_null=True)


class MembershipSerializer(serializers.ModelSerializer):
    role_code = serializers.CharField(source="role.code", read_only=True)
    user_id = serializers.UUIDField(source="user.id", read_only=True)
    user_full_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = Membership
        fields = [
            "id",
            "user_id",
            "user_full_name",
            "role_code",
            "relationship",
            "status",
            "is_primary",
            "joined_at",
            "ended_at",
        ]
        read_only_fields = fields


class MembershipRoleChangeSerializer(serializers.Serializer):
    role_code = serializers.CharField(max_length=64)


class InvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invitation
        fields = [
            "id",
            "elder_id",
            "invite_code",
            "status",
            "expires_at",
            "accepted_at",
            "created_at",
        ]
        read_only_fields = fields


class InvitationCreateSerializer(serializers.Serializer):
    expires_at = serializers.DateTimeField()

    def validate_expires_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Expiration must be in the future.")
        return value


class InvitationAcceptSerializer(serializers.Serializer):
    invite_code = serializers.CharField(max_length=64)


class EmergencyRecipientSerializer(serializers.ModelSerializer):
    membership_id = serializers.UUIDField(source="membership.id", read_only=True)
    user_id = serializers.UUIDField(source="membership.user.id", read_only=True)
    user_full_name = serializers.CharField(source="membership.user.full_name", read_only=True)

    class Meta:
        model = EmergencyRecipient
        fields = [
            "id",
            "membership_id",
            "user_id",
            "user_full_name",
            "priority",
            "status",
        ]
        read_only_fields = fields


class EmergencyRecipientConfigureSerializer(serializers.Serializer):
    membership_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=True,
    )


class PermissionCheckSerializer(serializers.Serializer):
    permission_code = serializers.CharField(max_length=64)


class PermissionCheckResponseSerializer(serializers.Serializer):
    allowed = serializers.BooleanField()


class PermissionsListSerializer(serializers.Serializer):
    permissions = serializers.ListField(child=serializers.CharField())
