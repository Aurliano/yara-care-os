"""Notification domain exceptions."""


class NotificationError(Exception):
    """Base exception for Notification domain errors."""


class AlertNotFoundError(NotificationError):
    """Raised when a caregiver alert cannot be found."""


class ElderNotFoundError(NotificationError):
    """Raised when the elder for an alert does not exist."""
