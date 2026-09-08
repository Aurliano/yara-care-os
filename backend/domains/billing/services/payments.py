"""Payment attempt audit and lifecycle services."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from django.db import transaction

from domains.billing.enums import PaymentAttemptStatus, PaymentProviderType
from domains.billing.exceptions import InvoiceNotFoundError, PaymentAttemptError
from domains.billing.models import Invoice, PaymentAttempt


def get_payment_attempt_by_idempotency_key(idempotency_key: str) -> PaymentAttempt | None:
    return PaymentAttempt.objects.filter(idempotency_key=idempotency_key).first()


def get_payment_attempt_by_provider_reference(provider_reference: str) -> PaymentAttempt | None:
    return PaymentAttempt.objects.filter(provider_reference=provider_reference).first()


@transaction.atomic
def record_payment_attempt(
    *,
    invoice_id: uuid.UUID,
    provider: str = PaymentProviderType.FAKE,
    idempotency_key: str,
    amount: Decimal | None = None,
    provider_reference: str = "",
) -> PaymentAttempt:
    existing = get_payment_attempt_by_idempotency_key(idempotency_key)
    if existing:
        return existing

    try:
        invoice = Invoice.objects.get(pk=invoice_id)
    except Invoice.DoesNotExist:
        raise InvoiceNotFoundError(f"Invoice {invoice_id} not found") from None
    attempt_amount = amount if amount is not None else invoice.total_amount

    return PaymentAttempt.objects.create(
        invoice=invoice,
        provider=provider,
        provider_reference=provider_reference,
        idempotency_key=idempotency_key,
        amount=attempt_amount,
        status=PaymentAttemptStatus.INITIATED,
    )


@transaction.atomic
def update_payment_attempt_status(
    *,
    attempt_id: uuid.UUID,
    status: str,
    provider_reference: str | None = None,
    raw_payload: dict[str, Any] | None = None,
) -> PaymentAttempt:
    attempt = PaymentAttempt.objects.select_for_update().get(pk=attempt_id)
    attempt.status = status
    update_fields = ["status"]

    if provider_reference is not None:
        attempt.provider_reference = provider_reference
        update_fields.append("provider_reference")

    if raw_payload is not None:
        attempt.raw_payload = raw_payload
        update_fields.append("raw_payload")

    attempt.save(update_fields=update_fields)
    return attempt
