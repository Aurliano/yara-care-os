from django.db import models


class CareActivityStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    PAUSED = "PAUSED", "Paused"
    ENDED = "ENDED", "Ended"
    CANCELLED = "CANCELLED", "Cancelled"


class CareActivityType(models.TextChoices):
    MEDICATION = "MEDICATION", "Medication"
    EXERCISE = "EXERCISE", "Exercise"
    DAILY_CHECK_IN = "DAILY_CHECK_IN", "Daily Check-in"
    GENERAL = "GENERAL", "General"


class CompletionState(models.TextChoices):
    MEDICATION_TAKEN = "MEDICATION_TAKEN", "Medication Taken"
    MEDICATION_MISSED = "MEDICATION_MISSED", "Medication Missed"
    CARE_ACTIVITY_COMPLETED = "CARE_ACTIVITY_COMPLETED", "Care Activity Completed"
    CARE_ACTIVITY_MISSED = "CARE_ACTIVITY_MISSED", "Care Activity Missed"
    CARE_ACTIVITY_CANCELLED = "CARE_ACTIVITY_CANCELLED", "Care Activity Cancelled"
    CARE_ACTIVITY_FAILED = "CARE_ACTIVITY_FAILED", "Care Activity Failed"


class WorkflowExecutionResultType(models.TextChoices):
    EXECUTION_CONFIRMED = "ExecutionConfirmed", "Execution Confirmed"
    EXECUTION_MISSED = "ExecutionMissed", "Execution Missed"
    EXECUTION_CANCELLED = "ExecutionCancelled", "Execution Cancelled"
    EXECUTION_FAILED = "ExecutionFailed", "Execution Failed"
