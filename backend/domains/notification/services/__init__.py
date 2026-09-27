"""Public Notification domain service interface."""

from domains.notification.services.alerts import get_alert, list_elder_alerts, record_caregiver_alert
from domains.notification.services.push import (
    LoggingPushProvider,
    MockPushProvider,
    PushNotificationProvider,
    PushResult,
    clear_device_tokens,
    dispatch_alert_push,
    get_caregiver_device_tokens_for_elder,
    get_push_provider,
    register_device_token,
    set_push_provider,
    unregister_device_token,
)

__all__ = [
    "LoggingPushProvider",
    "MockPushProvider",
    "PushNotificationProvider",
    "PushResult",
    "clear_device_tokens",
    "dispatch_alert_push",
    "get_alert",
    "get_caregiver_device_tokens_for_elder",
    "get_push_provider",
    "list_elder_alerts",
    "record_caregiver_alert",
    "register_device_token",
    "set_push_provider",
    "unregister_device_token",
]
