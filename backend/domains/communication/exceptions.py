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


class ProviderFailureReason:
    """Stable, vendor-neutral reasons clients may branch on.

    Vendor error codes stay server-side so clients never learn the provider.
    """

    NOT_CONFIGURED = "PROVIDER_NOT_CONFIGURED"
    REJECTED = "PROVIDER_REJECTED"
    UNREACHABLE = "PROVIDER_UNREACHABLE"
    BUSY = "PROVIDER_BUSY"
    INVALID_RESPONSE = "PROVIDER_INVALID_RESPONSE"


class CommunicationProviderError(CommunicationError):
    """Raised when the transport provider cannot complete a request."""

    def __init__(
        self,
        message: str,
        *,
        error_code: int | None = None,
        reason: str = ProviderFailureReason.REJECTED,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.reason = reason


class ProviderRoomNotFoundError(CommunicationError):
    """Raised when a provider room binding cannot be found."""


class MessageNotFoundError(CommunicationError):
    """Raised when a message cannot be found."""


class AttachmentNotFoundError(CommunicationError):
    """Raised when an attachment cannot be found."""


class InvalidMessageError(CommunicationError):
    """Raised when a message payload is invalid."""


class InvalidMediaError(CommunicationError):
    """Raised when an uploaded media file fails validation."""


class MediaNotFoundError(CommunicationError):
    """Raised when an attachment file does not exist on disk."""
