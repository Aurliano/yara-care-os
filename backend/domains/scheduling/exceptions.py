"""Scheduling domain exceptions."""


class SchedulingError(Exception):
    """Base exception for Scheduling domain errors."""


class ScheduleNotFoundError(SchedulingError):
    """Raised when a schedule definition cannot be found."""


class OccurrenceNotFoundError(SchedulingError):
    """Raised when an occurrence cannot be found."""


class InvalidScheduleStateError(SchedulingError):
    """Raised when a schedule operation conflicts with current status."""


class InvalidOccurrenceStateError(SchedulingError):
    """Raised when an occurrence operation conflicts with current status."""


class InvalidRecurrenceDefinitionError(SchedulingError):
    """Raised when recurrence_definition cannot be parsed or evaluated."""


class RescheduleCollisionError(SchedulingError):
    """Raised when a reschedule would conflict with another occurrence."""
