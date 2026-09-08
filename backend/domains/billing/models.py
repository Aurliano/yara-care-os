"""Billing domain models."""

from __future__ import annotations

import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from domains.billing.enums import (
    BillingInterval,
    Currency,
    InvoiceStatus,
    PaymentAttemptStatus,
    PaymentProviderType,
)


class PlanPrice(models.Model):
    """Commercial price definition for a Plan.

    Decoupled from technical Plan definition in Licensing domain.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan_code = models.CharField(max_length=64, db_index=True)
    interval = models.CharField(
        max_length=16,
        choices=BillingInterval.choices,
        default=BillingInterval.MONTHLY,
    )
    amount = models.DecimalField(max_digits=14, decimal_places=0)
    currency = models.CharField(
        max_length=16,
        choices=Currency.choices,
        default=Currency.TOMAN,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "billing_plan_price"
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gte=Decimal("0")),
                name="billing_plan_price_non_negative",
            ),
            models.UniqueConstraint(
                fields=["plan_code", "interval", "currency"],
                condition=Q(is_active=True),
                name="billing_plan_price_single_active_per_tier",
            ),
        ]

    def clean(self) -> None:
        if self.amount < Decimal("0"):
            raise ValidationError({"amount": "Price amount cannot be negative."})

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.plan_code}:{self.interval}:{self.amount} {self.currency}"


class Invoice(models.Model):
    """Billable financial obligation for an Elder context."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=64, unique=True, db_index=True)
    elder_id = models.UUIDField(db_index=True)
    payer_user_id = models.UUIDField(db_index=True)
    subscription_id = models.UUIDField(null=True, blank=True, db_index=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=0, default=Decimal("0"))
    currency = models.CharField(
        max_length=16,
        choices=Currency.choices,
        default=Currency.TOMAN,
    )
    status = models.CharField(
        max_length=16,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.UNPAID,
    )
    due_date = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "billing_invoice"
        constraints = [
            models.CheckConstraint(
                condition=Q(total_amount__gte=Decimal("0")),
                name="billing_invoice_total_non_negative",
            ),
        ]

    def clean(self) -> None:
        if self.total_amount < Decimal("0"):
            raise ValidationError({"total_amount": "Total amount cannot be negative."})

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.invoice_number}:{self.status}:{self.total_amount} {self.currency}"


class InvoiceLineItem(models.Model):
    """Itemized detail line on an Invoice."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="line_items",
    )
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=14, decimal_places=0)
    quantity = models.PositiveIntegerField(default=1)
    line_type = models.CharField(max_length=32, default="SUBSCRIPTION")

    class Meta:
        db_table = "billing_invoice_line_item"

    def __str__(self) -> str:
        return f"{self.invoice.invoice_number}:{self.description}:{self.amount}"


class PaymentAttempt(models.Model):
    """Immutable audit record of a payment attempt via a gateway provider."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="payment_attempts",
    )
    provider = models.CharField(
        max_length=32,
        choices=PaymentProviderType.choices,
        default=PaymentProviderType.FAKE,
    )
    provider_reference = models.CharField(max_length=255, blank=True, default="", db_index=True)
    idempotency_key = models.CharField(max_length=128, unique=True, db_index=True)
    amount = models.DecimalField(max_digits=14, decimal_places=0)
    status = models.CharField(
        max_length=16,
        choices=PaymentAttemptStatus.choices,
        default=PaymentAttemptStatus.INITIATED,
    )
    raw_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "billing_payment_attempt"

    def __str__(self) -> str:
        return f"{self.invoice.invoice_number}:{self.provider}:{self.status}:{self.amount}"
