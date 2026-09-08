"""Resolve the configured PaymentProvider adapter."""

from __future__ import annotations

from django.conf import settings

from infrastructure.payment.exceptions import PaymentFailureReason, PaymentProviderError
from infrastructure.payment.ports import PaymentProvider

_FAKE_SINGLETON: PaymentProvider | None = None


def get_payment_provider() -> PaymentProvider:
    """Resolve the active payment provider based on Django settings."""
    provider_name = getattr(settings, "PAYMENT_PROVIDER", "fake").lower().strip()

    if provider_name == "fake":
        return _get_fake_provider()

    if provider_name == "zarinpal":
        from infrastructure.payment.zarinpal import ZarinpalPaymentProvider

        return ZarinpalPaymentProvider()

    raise PaymentProviderError(
        f"Unsupported payment provider '{provider_name}'.",
        reason=PaymentFailureReason.UNSUPPORTED_PROVIDER,
    )


def _get_fake_provider() -> PaymentProvider:
    global _FAKE_SINGLETON
    if _FAKE_SINGLETON is None:
        from infrastructure.payment.fake import FakePaymentProvider

        _FAKE_SINGLETON = FakePaymentProvider()
    return _FAKE_SINGLETON


def reset_fake_provider() -> None:
    """Reset the fake singleton instance (used in tests)."""
    global _FAKE_SINGLETON
    if _FAKE_SINGLETON is not None and hasattr(_FAKE_SINGLETON, "reset"):
        _FAKE_SINGLETON.reset()
    _FAKE_SINGLETON = None
