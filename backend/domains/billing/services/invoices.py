"""Invoice lifecycle services."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.utils import timezone

from domains.billing.enums import Currency, InvoiceStatus
from domains.billing.exceptions import InvalidInvoiceStateError, InvoiceNotFoundError
from domains.billing.models import Invoice, InvoiceLineItem


def generate_invoice_number() -> str:
    now = timezone.now()
    unique_suffix = uuid.uuid4().hex[:8].upper()
    return f"INV-{now.strftime('%Y%m')}-{unique_suffix}"


def get_invoice(invoice_id: uuid.UUID) -> Invoice:
    try:
        return Invoice.objects.prefetch_related("line_items", "payment_attempts").get(pk=invoice_id)
    except Invoice.DoesNotExist as exc:
        raise InvoiceNotFoundError(f"Invoice {invoice_id} not found.") from exc


def get_invoices_for_elder(elder_id: uuid.UUID) -> list[Invoice]:
    return list(
        Invoice.objects.filter(elder_id=elder_id)
        .prefetch_related("line_items")
        .order_by("-created_at")
    )


@transaction.atomic
def create_invoice(
    *,
    elder_id: uuid.UUID,
    payer_user_id: uuid.UUID,
    subscription_id: uuid.UUID | None = None,
    line_items_data: list[dict[str, Any]] | None = None,
    currency: str = Currency.TOMAN,
    due_date: datetime | None = None,
) -> Invoice:
    invoice = Invoice.objects.create(
        invoice_number=generate_invoice_number(),
        elder_id=elder_id,
        payer_user_id=payer_user_id,
        subscription_id=subscription_id,
        total_amount=Decimal("0"),
        currency=currency,
        status=InvoiceStatus.UNPAID,
        due_date=due_date,
    )

    total = Decimal("0")
    if line_items_data:
        for item in line_items_data:
            line_amount = Decimal(str(item["amount"]))
            quantity = int(item.get("quantity", 1))
            total += line_amount * quantity
            InvoiceLineItem.objects.create(
                invoice=invoice,
                description=item["description"],
                amount=line_amount,
                quantity=quantity,
                line_type=item.get("line_type", "SUBSCRIPTION"),
            )

    invoice.total_amount = total
    invoice.save(update_fields=["total_amount"])
    return invoice


@transaction.atomic
def settle_invoice(*, invoice_id: uuid.UUID, paid_at: datetime | None = None) -> Invoice:
    invoice = Invoice.objects.select_for_update().get(pk=invoice_id)
    if invoice.status == InvoiceStatus.PAID:
        return invoice

    if invoice.status != InvoiceStatus.UNPAID:
        raise InvalidInvoiceStateError(f"Cannot settle invoice with status '{invoice.status}'.")

    invoice.status = InvoiceStatus.PAID
    invoice.paid_at = paid_at or timezone.now()
    invoice.save(update_fields=["status", "paid_at"])
    return invoice


@transaction.atomic
def void_invoice(*, invoice_id: uuid.UUID) -> Invoice:
    invoice = Invoice.objects.select_for_update().get(pk=invoice_id)
    if invoice.status == InvoiceStatus.PAID:
        raise InvalidInvoiceStateError("Cannot void a paid invoice.")

    invoice.status = InvoiceStatus.VOID
    invoice.save(update_fields=["status"])
    return invoice
