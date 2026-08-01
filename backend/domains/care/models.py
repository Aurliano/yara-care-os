"""Care domain models."""

from __future__ import annotations

import uuid

from django.db import models

from domains.care.enums import CareActivityStatus, CareActivityType, CompletionState


class CareActivity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    elder = models.ForeignKey(
        "identity_access.Elder",
        on_delete=models.PROTECT,
        related_name="care_activities",
    )
    activity_type = models.CharField(max_length=32, choices=CareActivityType.choices)
    status = models.CharField(
        max_length=16,
        choices=CareActivityStatus.choices,
        default=CareActivityStatus.ACTIVE,
    )
    schedule_definition = models.OneToOneField(
        "scheduling.ScheduleDefinition",
        on_delete=models.PROTECT,
        related_name="care_activity",
    )
    workflow_definition = models.ForeignKey(
        "workflow.WorkflowDefinition",
        on_delete=models.PROTECT,
        related_name="care_activities",
    )
    display_title = models.CharField(max_length=128)
    display_subtitle = models.CharField(max_length=255, blank=True, default="")
    display_icon = models.CharField(max_length=64, blank=True, default="")
    confirmation_requirement = models.JSONField(default=dict)
    compartment_assignment_reference = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "care_activity"
        indexes = [
            models.Index(fields=["elder", "status"], name="care_activity_elder_status_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.display_title}:{self.status}"


class Prescription(models.Model):
    care_activity = models.OneToOneField(
        CareActivity,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="prescription",
    )
    medication_reference = models.CharField(max_length=128)
    dosage_information = models.CharField(max_length=255)
    elder_friendly_description = models.TextField()
    personalized_description = models.TextField(blank=True, default="")
    media_reference = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "care_prescription"

    def __str__(self) -> str:
        return f"{self.care_activity_id}:{self.medication_reference}"


class CareCompletion(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    care_activity = models.ForeignKey(
        CareActivity,
        on_delete=models.PROTECT,
        related_name="completions",
    )
    occurrence_id = models.UUIDField()
    workflow_execution_id = models.UUIDField(unique=True)
    completion_state = models.CharField(max_length=32, choices=CompletionState.choices)
    interpreted_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "care_completion"
        indexes = [
            models.Index(fields=["care_activity", "interpreted_at"], name="care_completion_history_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.workflow_execution_id}:{self.completion_state}"
