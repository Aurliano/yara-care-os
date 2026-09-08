"""Licensing domain exceptions."""


class LicensingError(Exception):
    """Base exception for Licensing domain errors."""


class InvalidLicenseStateError(LicensingError):
    """Raised when a license operation violates lifecycle rules."""


class InvalidEntitlementError(LicensingError):
    """Raised when entitlement configuration or values are invalid."""


class LicenseNotFoundError(LicensingError):
    """Raised when no applicable license exists for an Elder."""


class InvalidSubscriptionStateError(LicensingError):
    """Raised when a subscription operation violates lifecycle rules."""


class SubscriptionNotFoundError(LicensingError):
    """Raised when a requested subscription cannot be found."""
