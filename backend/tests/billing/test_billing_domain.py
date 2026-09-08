"""Unit tests for Billing domain models and services."""

import uuid
from decimal import Decimal
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from domains.billing.enums import (
    BillingInterval,
    Currency,
    InvoiceStatus,
    PaymentAttemptStatus,
    PaymentProviderType,
)
from domains.billing.exceptions import InvalidInvoiceStateError, InvoiceNotFoundError
from domains.billing.models import Invoice, InvoiceLineItem, PaymentAttempt, PlanPrice
from domains.billing.services.invoices import (
    create_invoice,
    get_invoice,
    get_invoices_for_elder,
    settle_invoice,
    void_invoice,
)
from domains.billing.services.payments import (
    get_payment_attempt_by_idempotency_key,
    get_payment_attempt_by_provider_reference,
    record_payment_attempt,
    update_payment_attempt_status,
)
from domains.billing.services.pricing import create_plan_price, get_active_price


@pytest.mark.django_db
def test_plan_price_creation_and_query():
    price = create_plan_price(
        plan_code="PLUS",
        amount=Decimal("390000"),
        interval=BillingInterval.MONTHLY,
        currency=Currency.TOMAN,
    )
    assert price.is_active is True
    assert price.amount == Decimal("390000")

    found = get_active_price(
        plan_code="PLUS",
        interval=BillingInterval.MONTHLY,
        currency=Currency.TOMAN,
    )
    assert found is not None
    assert found.id == price.id

    # Non-existing price returns None
    assert get_active_price("NON_EXISTENT") is None


@pytest.mark.django_db
def test_plan_price_single_active_constraint():
    create_plan_price(
        plan_code="PLUS",
        amount=Decimal("390000"),
        interval=BillingInterval.MONTHLY,
        currency=Currency.TOMAN,
        is_active=True,
    )
    # Duplicate active price for same tier raises ValidationError/IntegrityError
    with pytest.raises((ValidationError, IntegrityError)):
        PlanPrice.objects.create(
            plan_code="PLUS",
            amount=Decimal("450000"),
            interval=BillingInterval.MONTHLY,
            currency=Currency.TOMAN,
            is_active=True,
        )


@pytest.mark.django_db
def test_plan_price_negative_amount_rejected():
    with pytest.raises(ValidationError):
        invalid_price = PlanPrice(
            plan_code="PLUS",
            amount=Decimal("-100"),
            interval=BillingInterval.MONTHLY,
            currency=Currency.TOMAN,
        )
        invalid_price.save()


@pytest.mark.django_db
def test_invoice_creation_and_total_calculation():
    elder_id = uuid.uuid4()
    payer_id = uuid.uuid4()
    sub_id = uuid.uuid4()

    line_items = [
        {"description": "Plus Plan Monthly Subscription", "amount": Decimal("390000"), "quantity": 1},
        {"description": "Smart Pillbox Lease Fee", "amount": Decimal("50000"), "quantity": 1},
    ]

    invoice = create_invoice(
        elder_id=elder_id,
        payer_user_id=payer_id,
        subscription_id=sub_id,
        line_items_data=line_items,
        currency=Currency.TOMAN,
    )

    assert invoice.status == InvoiceStatus.UNPAID
    assert invoice.elder_id == elder_id
    assert invoice.payer_user_id == payer_id
    assert invoice.subscription_id == sub_id
    assert invoice.total_amount == Decimal("440000")
    assert invoice.line_items.count() == 2
    assert invoice.paid_at is None
    assert invoice.invoice_number.startswith("INV-")


@pytest.mark.django_db
def test_invoice_settlement_and_void():
    elder_id = uuid.uuid4()
    payer_id = uuid.uuid4()
    invoice = create_invoice(
        elder_id=elder_id,
        payer_user_id=payer_id,
        line_items_data=[{"description": "Test item", "amount": Decimal("100000"), "quantity": 1}],
    )

    # Settle invoice
    paid_invoice = settle_invoice(invoice_id=invoice.id)
    assert paid_invoice.status == InvoiceStatus.PAID
    assert paid_invoice.paid_at is not None

    # Settling an already paid invoice is idempotent
    re_settled = settle_invoice(invoice_id=invoice.id)
    assert re_settled.status == InvoiceStatus.PAID

    # Cannot void a paid invoice
    with pytest.raises(InvalidInvoiceStateError):
        void_invoice(invoice_id=invoice.id)


@pytest.mark.django_db
def test_void_unpaid_invoice():
    elder_id = uuid.uuid4()
    payer_id = uuid.uuid4()
    invoice = create_invoice(
        elder_id=elder_id,
        payer_user_id=payer_id,
        line_items_data=[{"description": "Item", "amount": Decimal("10000")}],
    )
    voided = void_invoice(invoice_id=invoice.id)
    assert voided.status == InvoiceStatus.VOID

    # Cannot settle a voided invoice
    with pytest.raises(InvalidInvoiceStateError):
        settle_invoice(invoice_id=invoice.id)


@pytest.mark.django_db
def test_get_invoices_query():
    elder_id = uuid.uuid4()
    payer_id = uuid.uuid4()
    inv1 = create_invoice(elder_id=elder_id, payer_user_id=payer_id)
    inv2 = create_invoice(elder_id=elder_id, payer_user_id=payer_id)

    invoices = get_invoices_for_elder(elder_id=elder_id)
    assert len(invoices) == 2
    assert {i.id for i in invoices} == {inv1.id, inv2.id}

    retrieved = get_invoice(inv1.id)
    assert retrieved.id == inv1.id

    with pytest.raises(InvoiceNotFoundError):
        get_invoice(uuid.uuid4())


@pytest.mark.django_db
def test_payment_attempt_recording_and_idempotency():
    elder_id = uuid.uuid4()
    payer_id = uuid.uuid4()
    invoice = create_invoice(
        elder_id=elder_id,
        payer_user_id=payer_id,
        line_items_data=[{"description": "Subscription", "amount": Decimal("390000")}],
    )

    attempt1 = record_payment_attempt(
        invoice_id=invoice.id,
        provider=PaymentProviderType.ZARINPAL,
        idempotency_key="tx-123456-abc",
    )
    assert attempt1.status == PaymentAttemptStatus.INITIATED
    assert attempt1.amount == Decimal("390000")
    assert attempt1.provider == PaymentProviderType.ZARINPAL

    # Idempotent re-recording with same idempotency_key returns existing attempt
    attempt2 = record_payment_attempt(
        invoice_id=invoice.id,
        provider=PaymentProviderType.ZARINPAL,
        idempotency_key="tx-123456-abc",
    )
    assert attempt2.id == attempt1.id


@pytest.mark.django_db
def test_payment_attempt_lifecycle_updates():
    elder_id = uuid.uuid4()
    payer_id = uuid.uuid4()
    invoice = create_invoice(
        elder_id=elder_id,
        payer_user_id=payer_id,
        line_items_data=[{"description": "Item", "amount": Decimal("10000")}],
    )

    attempt = record_payment_attempt(
        invoice_id=invoice.id,
        provider=PaymentProviderType.ZARINPAL,
        idempotency_key="unique-key-xyz",
    )

    # 1. Update with provider authority upon redirect
    updated = update_payment_attempt_status(
        attempt_id=attempt.id,
        status=PaymentAttemptStatus.REDIRECTED,
        provider_reference="A00000000000000000000000000000000001",
    )
    assert updated.status == PaymentAttemptStatus.REDIRECTED
    assert updated.provider_reference == "A00000000000000000000000000000000001"

    # Query by provider reference
    by_ref = get_payment_attempt_by_provider_reference("A00000000000000000000000000000000001")
    assert by_ref is not None
    assert by_ref.id == attempt.id

    # 2. Update upon successful verification callback
    success_payload = {"ref_id": "12345678", "card_pan": "5022-29**-****-1234"}
    verified = update_payment_attempt_status(
        attempt_id=attempt.id,
        status=PaymentAttemptStatus.SUCCESSFUL,
        raw_payload=success_payload,
    )
    assert verified.status == PaymentAttemptStatus.SUCCESSFUL
    assert verified.raw_payload["ref_id"] == "12345678"
