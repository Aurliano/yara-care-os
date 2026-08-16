"""Communication domain exceptions."""


class CommunicationError(Exception):
    """Base exception for Communication domain errors."""


class ContactNotFoundError(CommunicationError):
    """Raised when a contact cannot be found."""


class SessionNotFoundError(CommunicationError):
    """Raised when a communication session cannot be found."""


class CallAttemptNotFoundError(CommunicationError):
    """Raised when a call attempt cannot be found."""


class InvalidSessionStateError(CommunicationError):
    """Raised when a session operation conflicts with current status."""


class ActiveSessionExistsError(InvalidSessionStateError):
    """Raised when an elder already has a non-terminal communication session."""


class InvalidContactStateError(CommunicationError):
    """Raised when a contact operation is not allowed."""


class EntitlementDeniedError(CommunicationError):
    """Raised when licensing blocks a gated communication capability."""


class AuthorizationDeniedError(CommunicationError):
    """Raised when identity authorization blocks an operation."""


class CommunicationProviderError(CommunicationError):
    """Raised when the transport provider cannot complete a request."""

    def __init__(self, message: str, *, error_code: int | None = None) -> None:
        super().__init__(message)
        self.error_code = error_code


class ProviderRoomNotFoundError(CommunicationError):
    """Raised when a provider room binding cannot be found."""
