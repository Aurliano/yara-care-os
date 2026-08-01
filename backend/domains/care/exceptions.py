"""Care domain exceptions."""


class CareError(Exception):
    """Base exception for Care domain errors."""


class CareActivityNotFoundError(CareError):
    """Raised when a care activity cannot be found."""


class PrescriptionNotFoundError(CareError):
    """Raised when a prescription cannot be found."""


class InvalidCareActivityStateError(CareError):
    """Raised when an operation conflicts with current activity status."""


class CareCompletionNotFoundError(CareError):
    """Raised when a care completion cannot be found."""


class InvalidExecutionResultError(CareError):
    """Raised when an execution result cannot be interpreted."""


class ElderNotFoundError(CareError):
    """Raised when the referenced elder does not exist."""
