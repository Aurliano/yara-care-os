"""Identity & Access domain exceptions."""


class IdentityAccessError(Exception):
    """Base exception for Identity & Access domain errors."""


class AuthorizationError(IdentityAccessError):
    """Raised when an actor lacks required access."""


class InvalidMembershipStateError(IdentityAccessError):
    """Raised when a membership operation violates lifecycle rules."""


class InvalidInvitationStateError(IdentityAccessError):
    """Raised when an invitation operation violates lifecycle rules."""


class LastPrimaryCaregiverError(IdentityAccessError):
    """Raised when an operation would leave an Elder without management access."""
