"""Workflow API serializers."""

from rest_framework import serializers

from domains.workflow.models import WorkflowDefinition, WorkflowExecution


class WorkflowDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowDefinition
        fields = ["id", "code", "name", "status", "definition", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class WorkflowExecutionSerializer(serializers.ModelSerializer):
    occurrence_id = serializers.UUIDField(read_only=True)
    workflow_definition_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = WorkflowExecution
        fields = [
            "id",
            "occurrence_id",
            "workflow_definition_id",
            "status",
            "current_step",
            "postpone_count",
            "retry_count",
            "escalation_index",
            "current_action",
            "active_until",
            "started_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ConfirmationEvidenceSubmitSerializer(serializers.Serializer):
    evidence_type = serializers.CharField(max_length=64)
    source_type = serializers.CharField(max_length=32)
    source_reference = serializers.CharField(max_length=255)
    actor_user_id = serializers.UUIDField(required=False, allow_null=True)
    payload = serializers.JSONField(required=False, default=dict)


class ActionResultSubmitSerializer(serializers.Serializer):
    action_reference = serializers.CharField(max_length=128)
    action_type = serializers.CharField(max_length=64)
    result_status = serializers.CharField(max_length=16)
    payload = serializers.JSONField(required=False, default=dict)
