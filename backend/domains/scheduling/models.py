"""Scheduling domain models."""

from __future__ import annotations

import uuid

from django.db import models

from domains.scheduling.enums import (
    OccurrenceStatus,
    ScheduleExceptionType,
    ScheduleStatus,
)


class ScheduleDefinition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner_reference = models.CharField(max_length=255)
    recurrence_definition = models.JSONField()
    timezone = models.CharField(max_length=64)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=16,
        choices=ScheduleStatus.choices,
        default=ScheduleStatus.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "scheduling_schedule_definition"
        indexes = [
            models.Index(fields=["owner_reference"], name="sched_owner_ref_idx"),
            models.Index(fields=["status"], name="sched_status_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.owner_reference}:{self.status}"


class ScheduleException(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schedule_definition = models.ForeignKey(
        ScheduleDefinition,
        on_delete=models.CASCADE,
        related_name="exceptions",
    )
    original_time = models.DateTimeField()
    replacement_time = models.DateTimeField(null=True, blank=True)
    exception_type = models.CharField(max_length=16, choices=ScheduleExceptionType.choices)
    reason = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "scheduling_schedule_exception"
        constraints = [
            models.UniqueConstraint(
                fields=["schedule_definition", "original_time"],
                name="scheduling_exception_unique_slot",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.exception_type}@{self.original_time}"


class Occurrence(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    schedule_definition = models.ForeignKey(
        ScheduleDefinition,
        on_delete=models.CASCADE,
        related_name="occurrences",
    )
    scheduled_for = models.DateTimeField()
    status = models.CharField(
        max_length=16,
        choices=OccurrenceStatus.choices,
        default=OccurrenceStatus.SCHEDULED,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "scheduling_occurrence"
        indexes = [
            models.Index(fields=["schedule_definition", "scheduled_for"], name="sched_occ_scheduled_idx"),
            models.Index(fields=["status", "scheduled_for"], name="sched_occ_status_due_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["schedule_definition", "scheduled_for"],
                name="scheduling_occurrence_unique_slot",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.schedule_definition_id}@{self.scheduled_for}:{self.status}"
