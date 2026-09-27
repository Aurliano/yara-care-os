"""Push notification provider abstraction and delivery service."""

from __future__ import annotations

import abc
import logging
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from common.observability.metrics import increment

if TYPE_CHECKING:
    from domains.notification.models import CaregiverAlert

logger = logging.getLogger("yara.notification.push")


@dataclass(frozen=True)
class PushResult:
    """Outcome of an individual push notification delivery attempt."""

    success: bool
    provider_message_id: str | None = None
    error: str | None = None


class PushNotificationProvider(abc.ABC):
    """Abstract push notification provider interface."""

    @abc.abstractmethod
    def send_push_notification(
        self,
        *,
        recipient_token: str,
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
    ) -> PushResult:
        """Send a single push notification to a device token.

        Implementations must not crash unhandled on transient network errors.
        """
        raise NotImplementedError


class LoggingPushProvider(PushNotificationProvider):
    """Default no-op / logging provider suitable for environments without external push keys."""

    def send_push_notification(
        self,
        *,
        recipient_token: str,
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
    ) -> PushResult:
        logger.info(
            "LoggingPushProvider: push dispatched to token=%s title=%s data=%s",
            recipient_token[:8] + "..." if len(recipient_token) > 8 else recipient_token,
            title,
            data,
        )
        return PushResult(
            success=True,
            provider_message_id=f"log-{uuid.uuid4().hex[:12]}",
        )


class MockPushProvider(PushNotificationProvider):
    """In-memory mock provider for testing failure and retry semantics."""

    def __init__(
        self,
        *,
        should_fail: bool = False,
        fail_exception: Exception | None = None,
    ) -> None:
        self.should_fail = should_fail
        self.fail_exception = fail_exception
        self.dispatched: list[dict[str, Any]] = []

    def send_push_notification(
        self,
        *,
        recipient_token: str,
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
    ) -> PushResult:
        if self.fail_exception:
            raise self.fail_exception
        if self.should_fail:
            return PushResult(success=False, error="Provider delivery failed (simulated).")

        self.dispatched.append(
            {
                "recipient_token": recipient_token,
                "title": title,
                "body": body,
                "data": data or {},
            }
        )
        return PushResult(
            success=True,
            provider_message_id=f"mock-{uuid.uuid4().hex[:8]}",
        )


_CURRENT_PROVIDER: PushNotificationProvider = LoggingPushProvider()
_DEVICE_TOKENS: dict[uuid.UUID, set[str]] = {}


def get_push_provider() -> PushNotificationProvider:
    """Return the active push notification provider."""
    return _CURRENT_PROVIDER


def set_push_provider(provider: PushNotificationProvider | None) -> None:
    """Set the active push notification provider (or reset to LoggingPushProvider if None)."""
    global _CURRENT_PROVIDER
    _CURRENT_PROVIDER = provider or LoggingPushProvider()


def register_device_token(user_id: uuid.UUID, token: str) -> None:
    """Register a device push token for a caregiver user."""
    tokens = _DEVICE_TOKENS.setdefault(user_id, set())
    tokens.add(token)


def unregister_device_token(user_id: uuid.UUID, token: str) -> None:
    """Unregister a device push token for a caregiver user."""
    if user_id in _DEVICE_TOKENS:
        _DEVICE_TOKENS[user_id].discard(token)


def clear_device_tokens() -> None:
    """Clear all registered in-memory device tokens (primarily for test cleanup)."""
    _DEVICE_TOKENS.clear()


def get_caregiver_device_tokens_for_elder(elder_id: uuid.UUID) -> list[str]:
    """Retrieve all registered device push tokens for active caregivers of an elder."""
    from domains.identity_access.enums import MembershipStatus
    from domains.identity_access.models import Membership

    active_user_ids = list(
        Membership.objects.filter(
            elder_id=elder_id,
            status=MembershipStatus.ACTIVE,
        ).values_list("user_id", flat=True)
    )
    tokens: list[str] = []
    for uid in active_user_ids:
        tokens.extend(_DEVICE_TOKENS.get(uid, []))
    return sorted(tokens)


def dispatch_alert_push(
    alert: CaregiverAlert,
    tokens: list[str] | None = None,
) -> list[PushResult]:
    """Attempt push delivery for a CaregiverAlert.

    CRITICAL DOMAIN RULE:
    CaregiverAlert != PushNotification.
    CaregiverAlert is the durable business fact. PushNotification is only a delivery mechanism.
    Push failure (FCM offline, network down, permission denied, provider failure)
    MUST NEVER delete, roll back, or invalidate the underlying CaregiverAlert.
    This function catches all exceptions and never raises to the caller.
    """
    provider = get_push_provider()

    if tokens is None:
        tokens = get_caregiver_device_tokens_for_elder(alert.elder_id)
        if not tokens:
            # Fallback channel token when no explicit device tokens are registered yet
            tokens = [f"elder-channel-{alert.elder_id}"]

    payload = {
        "alert_id": str(alert.id),
        "elder_id": str(alert.elder_id),
        "severity": alert.severity,
        "type": "alert",
    }

    results: list[PushResult] = []
    for token in tokens:
        increment("notification.delivery_attempted")
        try:
            res = provider.send_push_notification(
                recipient_token=token,
                title=alert.title,
                body=alert.body,
                data=payload,
            )
            if res.success:
                increment("notification.delivered")
                logger.info(
                    "Push notification delivered: alert_id=%s token=%s msg_id=%s",
                    alert.id,
                    token[:12] if len(token) > 12 else token,
                    res.provider_message_id,
                )
            else:
                increment("notification.failed")
                logger.warning(
                    "Push notification delivery failed by provider: alert_id=%s token=%s error=%s",
                    alert.id,
                    token[:12] if len(token) > 12 else token,
                    res.error,
                )
            results.append(res)
        except Exception as exc:  # noqa: BLE001 — Push failures must be completely isolated
            increment("notification.failed")
            logger.error(
                "Push notification unexpected exception: alert_id=%s token=%s error=%s",
                alert.id,
                token[:12] if len(token) > 12 else token,
                exc,
            )
            results.append(PushResult(success=False, error=str(exc)))

    return results
