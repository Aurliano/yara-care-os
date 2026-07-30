"""Workflow domain models."""

from __future__ import annotations

import uuid

from django.db import models

from domains.workflow.enums import (
    ActionResultStatus,
    EvidenceSourceType,
    ExecutionStatus,
    WorkflowDefinitionStatus,
)


class WorkflowDefinition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    status = models.CharField(
        max_length=16,
        choices=WorkflowDefinitionStatus.choices,
        default=WorkflowDefinitionStatus.ACTIVE,
    )
    definition = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "workflow_definition"

    def __str__(self) -> str:
        return self.code


class WorkflowExecution(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    occurrence = models.OneToOneField(
        "scheduling.Occurrence",
        on_delete=models.PROTECT,
        related_name="workflow_execution",
    )
    workflow_definition = models.ForeignKey(
        WorkflowDefinition,
        on_delete=models.PROTECT,
        related_name="executions",
    )
    status = models.CharField(
        max_length=16,
        choices=ExecutionStatus.choices,
        default=ExecutionStatus.PENDING,
    )
    current_step = models.CharField(max_length=64, default="initial")
    postpone_count = models.PositiveIntegerField(default=0)
    retry_count = models.PositiveIntegerField(default=0)
    escalation_index = models.PositiveIntegerField(default=0)
    current_action = models.JSONField(default=dict)
    active_until = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "workflow_execution"
        indexes = [
            models.Index(fields=["status", "active_until"], name="wf_exec_timeout_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.id}:{self.status}"


class ConfirmationEvidence(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow_execution = models.ForeignKey(
        WorkflowExecution,
        on_delete=models.CASCADE,
        related_name="evidence_records",
    )
    evidence_type = models.CharField(max_length=64)
    source_type = models.CharField(max_length=32, choices=EvidenceSourceType.choices)
    source_reference = models.CharField(max_length=255)
    actor_user_id = models.UUIDField(null=True, blank=True)
    payload = models.JSONField(default=dict)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "workflow_confirmation_evidence"
        constraints = [
            models.UniqueConstraint(
                fields=["workflow_execution", "source_type", "source_reference"],
                name="workflow_evidence_idempotent",
            ),
        ]


class ActionResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow_execution = models.ForeignKey(
        WorkflowExecution,
        on_delete=models.CASCADE,
        related_name="action_results",
    )
    action_reference = models.CharField(max_length=128)
    action_type = models.CharField(max_length=64)
    result_status = models.CharField(max_length=16, choices=ActionResultStatus.choices)
    payload = models.JSONField(default=dict)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "workflow_action_result"
        constraints = [
            models.UniqueConstraint(
                fields=["workflow_execution", "action_reference"],
                name="workflow_action_result_idempotent",
            ),
        ]
