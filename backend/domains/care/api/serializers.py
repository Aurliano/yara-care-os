"""Care API serializers."""

from rest_framework import serializers

from domains.care.models import CareActivity, CareCompletion, Prescription


class CareActivitySerializer(serializers.ModelSerializer):
    elder_id = serializers.UUIDField(read_only=True)
    schedule_definition_id = serializers.UUIDField(read_only=True)
    workflow_definition_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = CareActivity
        fields = [
            "id",
            "elder_id",
            "activity_type",
            "status",
            "schedule_definition_id",
            "workflow_definition_id",
            "display_title",
            "display_subtitle",
            "display_icon",
            "confirmation_requirement",
            "compartment_assignment_reference",
            "created_at",
            "updated_at",
        ]


class CareActivityCreateSerializer(serializers.Serializer):
    activity_type = serializers.CharField(max_length=32)
    workflow_definition_id = serializers.UUIDField()
    recurrence_definition = serializers.DictField()
    timezone_name = serializers.CharField(max_length=64)
    start_at = serializers.DateTimeField()
    end_at = serializers.DateTimeField(required=False, allow_null=True)
    display_title = serializers.CharField(max_length=128)
    display_subtitle = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    display_icon = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")
    confirmation_requirement = serializers.DictField(required=False)
    compartment_assignment_reference = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        default="",
    )


class CareActivityUpdateSerializer(serializers.Serializer):
    display_title = serializers.CharField(max_length=128, required=False)
    display_subtitle = serializers.CharField(max_length=255, required=False, allow_blank=True)
    display_icon = serializers.CharField(max_length=64, required=False, allow_blank=True)
    confirmation_requirement = serializers.DictField(required=False)
    compartment_assignment_reference = serializers.CharField(max_length=255, required=False, allow_blank=True)
    recurrence_definition = serializers.DictField(required=False)
    timezone_name = serializers.CharField(max_length=64, required=False)
    start_at = serializers.DateTimeField(required=False)
    end_at = serializers.DateTimeField(required=False, allow_null=True)


class PrescriptionSerializer(serializers.ModelSerializer):
    care_activity = CareActivitySerializer(read_only=True)

    class Meta:
        model = Prescription
        fields = [
            "care_activity_id",
            "care_activity",
            "medication_reference",
            "dosage_information",
            "elder_friendly_description",
            "personalized_description",
            "media_reference",
        ]


class PrescriptionCreateSerializer(serializers.Serializer):
    workflow_definition_id = serializers.UUIDField()
    recurrence_definition = serializers.DictField()
    timezone_name = serializers.CharField(max_length=64)
    start_at = serializers.DateTimeField()
    end_at = serializers.DateTimeField(required=False, allow_null=True)
    display_title = serializers.CharField(max_length=128)
    display_subtitle = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    display_icon = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")
    confirmation_requirement = serializers.DictField(required=False)
    compartment_assignment_reference = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        default="",
    )
    medication_reference = serializers.CharField(max_length=128)
    dosage_information = serializers.CharField(max_length=255)
    elder_friendly_description = serializers.CharField()
    personalized_description = serializers.CharField(required=False, allow_blank=True, default="")
    media_reference = serializers.UUIDField(required=False, allow_null=True)


class PrescriptionUpdateSerializer(CareActivityUpdateSerializer):
    medication_reference = serializers.CharField(max_length=128, required=False)
    dosage_information = serializers.CharField(max_length=255, required=False)
    elder_friendly_description = serializers.CharField(required=False)
    personalized_description = serializers.CharField(required=False, allow_blank=True)
    media_reference = serializers.UUIDField(required=False, allow_null=True)


class CareCompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareCompletion
        fields = [
            "id",
            "care_activity_id",
            "occurrence_id",
            "workflow_execution_id",
            "completion_state",
            "interpreted_at",
            "created_at",
        ]


class InterpretExecutionResultSerializer(serializers.Serializer):
    workflow_execution_id = serializers.UUIDField()
    result_type = serializers.CharField(max_length=32)
    occurred_at = serializers.DateTimeField(required=False, allow_null=True)
