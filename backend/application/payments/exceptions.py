"""Application-level payment coordinator exceptions."""

from __future__ import annotations


class PaymentCoordinatorError(Exception):
    """Base exception for payment coordinator failures."""


class PermissionDeniedError(PaymentCoordinatorError):
    """Raised when an actor lacks authority to operate on a subscription or invoice."""


class PlanPriceNotFoundError(PaymentCoordinatorError):
    """Raised when no active PlanPrice is found for the requested plan and interval."""


class PlanNotFoundError(PaymentCoordinatorError):
    """Raised when the requested plan code is invalid or inactive."""


class ElderNotFoundError(PaymentCoordinatorError):
    """Raised when the specified elder does not exist."""


class InvalidCallbackError(PaymentCoordinatorError):
    """Raised when a gateway callback has invalid or missing parameters."""


class PaymentAttemptNotFoundError(PaymentCoordinatorError):
    """Raised when no payment attempt matches the provider reference."""
