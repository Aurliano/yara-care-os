"""Payment domain event publication via Event Domain outbox."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from django.utils import timezone

from domains.billing.models import Invoice
from domains.event.services.recording import EventInput, publish_event, record_event

BILLING_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "billing.domains.yara.care")


def compute_payment_event_id(*, invoice_id: uuid.UUID) -> uuid.UUID:
    """Compute deterministic event identity for PaymentSucceeded.

    Guarantees that replaying settlement for the same invoice yields the identical event ID.
    """
    return uuid.uuid5(BILLING_NAMESPACE, f"PaymentSucceeded:{invoice_id}")


def publish_payment_succeeded_event(
    *,
    invoice: Invoice,
    provider_reference: str,
    tracking_code: str,
    amount: Decimal,
    currency: str,
) -> None:
    """Publish a provider-neutral PaymentSucceeded domain event via Event Domain."""
    event_id = compute_payment_event_id(invoice_id=invoice.id)
    payload: dict[str, Any] = {
        "invoice_id": str(invoice.id),
        "invoice_number": invoice.invoice_number,
        "elder_id": str(invoice.elder_id),
        "payer_user_id": str(invoice.payer_user_id),
        "subscription_id": str(invoice.subscription_id)
        if invoice.subscription_id
        else None,
        "amount": str(amount),
        "currency": currency,
        "provider_reference": provider_reference,
        "tracking_code": tracking_code,
    }

    event = record_event(
        EventInput(
            event_id=event_id,
            event_type="PaymentSucceeded",
            event_version=1,
            producer="billing",
            occurred_at=timezone.now(),
            payload=payload,
            correlation_id=str(invoice.id),
        )
    )
    publish_event(event_id=event.id)
