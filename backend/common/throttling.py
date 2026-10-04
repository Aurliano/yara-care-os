"""Rate throttling classes for sensitive authentication endpoints."""

from rest_framework.throttling import AnonRateThrottle


class AuthTokenRateThrottle(AnonRateThrottle):
    """Throttle for /api/v1/auth/token/ endpoint."""

    scope = "auth_token"


class AuthRegisterRateThrottle(AnonRateThrottle):
    """Throttle for /api/v1/auth/register/ endpoint."""

    scope = "auth_register"


class HubProvisionRateThrottle(AnonRateThrottle):
    """Throttle for /api/v1/hub/provision/authenticate/ endpoint."""

    scope = "hub_provision"
