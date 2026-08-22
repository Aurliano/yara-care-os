"""Notification domain enums."""

from django.db import models


class AlertSeverity(models.TextChoices):
    URGENT = "urgent", "Urgent"
    ATTENTION = "attention", "Attention"
    REMINDER = "reminder", "Reminder"
    INFORMATIONAL = "informational", "Informational"
