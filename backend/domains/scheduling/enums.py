from django.db import models


class ScheduleStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    PAUSED = "PAUSED", "Paused"
    ENDED = "ENDED", "Ended"
    CANCELLED = "CANCELLED", "Cancelled"


class OccurrenceStatus(models.TextChoices):
    SCHEDULED = "SCHEDULED", "Scheduled"
    DUE = "DUE", "Due"
    CANCELLED = "CANCELLED", "Cancelled"
    SKIPPED = "SKIPPED", "Skipped"


class ScheduleExceptionType(models.TextChoices):
    SKIP = "SKIP", "Skip"
    CANCEL = "CANCEL", "Cancel"
    RESCHEDULE = "RESCHEDULE", "Reschedule"
