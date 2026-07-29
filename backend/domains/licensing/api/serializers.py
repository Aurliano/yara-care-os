"""Licensing API serializers."""

from rest_framework import serializers

from domains.licensing.models import License, Plan


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ["id", "code", "name", "status", "created_at"]
        read_only_fields = fields


class PlanCreateSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=128)


class LicenseSerializer(serializers.ModelSerializer):
    plan_code = serializers.CharField(source="plan.code", read_only=True)
    elder_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = License
        fields = [
            "id",
            "elder_id",
            "plan_code",
            "status",
            "valid_from",
            "valid_until",
            "created_at",
        ]
        read_only_fields = fields


class LicenseActivateSerializer(serializers.Serializer):
    plan_code = serializers.CharField(max_length=64)
    valid_from = serializers.DateTimeField(required=False)
    valid_until = serializers.DateTimeField(required=False, allow_null=True)


class LicenseChangePlanSerializer(serializers.Serializer):
    plan_code = serializers.CharField(max_length=64)


class EntitlementCheckSerializer(serializers.Serializer):
    entitlement_key = serializers.CharField(max_length=64)


class EntitlementCheckResponseSerializer(serializers.Serializer):
    allowed = serializers.BooleanField()


class LimitResponseSerializer(serializers.Serializer):
    limit = serializers.IntegerField(allow_null=True)


class EntitlementMapSerializer(serializers.Serializer):
    entitlements = serializers.DictField()
