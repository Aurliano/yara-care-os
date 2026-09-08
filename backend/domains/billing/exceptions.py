"""Billing domain exceptions."""


class BillingError(Exception):
    """Base exception for Billing domain errors."""


class InvoiceNotFoundError(BillingError):
    """Raised when an invoice cannot be found."""


class InvalidInvoiceStateError(BillingError):
    """Raised when an invoice operation violates lifecycle rules."""


class PlanPriceNotFoundError(BillingError):
    """Raised when no active price exists for a plan."""


class PaymentAttemptError(BillingError):
    """Raised when payment attempt processing fails."""
