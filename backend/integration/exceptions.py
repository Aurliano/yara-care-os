"""Integration runtime exceptions."""


class IntegrationError(Exception):
    """Base exception for integration runtime errors."""


class ReplicaContextRequiredError(IntegrationError):
    """Raised when a Hub callback requires replica context."""


class HubProvisioningError(IntegrationError):
    """Raised when hub provisioning cannot proceed."""
