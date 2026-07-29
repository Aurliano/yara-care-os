"""Event domain exceptions."""


class EventError(Exception):
    """Base exception for Event domain errors."""


class EventImmutabilityError(EventError):
    """Raised when a recorded event would be mutated."""


class DuplicateEventError(EventError):
    """Raised when event_id conflicts with different event data."""
