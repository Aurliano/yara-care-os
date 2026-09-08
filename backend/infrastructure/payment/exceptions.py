"""Payment provider infrastructure exceptions."""

from __future__ import annotations

from enum import Enum


class PaymentFailureReason(str, Enum):
    NOT_CONFIGURED = "NOT_CONFIGURED"
    NETWORK_ERROR = "NETWORK_ERROR"
    TIMEOUT = "TIMEOUT"
    REQUEST_REJECTED = "REQUEST_REJECTED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    INVALID_RESPONSE = "INVALID_RESPONSE"
    UNSUPPORTED_PROVIDER = "UNSUPPORTED_PROVIDER"


class PaymentProviderError(Exception):
    """Base exception for payment provider infrastructure failures."""

    def __init__(
        self,
        message: str,
        *,
        reason: PaymentFailureReason = PaymentFailureReason.REQUEST_REJECTED,
    ) -> None:
        super().__init__(message)
        self.reason = reason


class PaymentProviderUnavailableError(PaymentProviderError):
    """Raised when connection failure, network error, or gateway outage occurs."""

    def __init__(self, message: str = "Payment provider unavailable.") -> None:
        super().__init__(message, reason=PaymentFailureReason.NETWORK_ERROR)


class PaymentProviderTimeoutError(PaymentProviderError):
    """Raised when payment provider HTTP request times out."""

    def __init__(self, message: str = "Payment provider request timed out.") -> None:
        super().__init__(message, reason=PaymentFailureReason.TIMEOUT)
