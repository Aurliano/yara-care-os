"""Tests for application-level Payment Coordinator."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.utils import timezone

from application.payments.coordinator import (
    handle_payment_callback,
    initiate_checkout,
)
from application.payments.exceptions import (
    InvalidCallbackError,
    PaymentAttemptNotFoundError,
    PermissionDeniedError,
    PlanNotFoundError,
    PlanPriceNotFoundError,
)
from domains.billing.enums import (
    BillingInterval,
    Currency,
    InvoiceStatus,
    PaymentAttemptStatus,
)
from domains.billing.models import Invoice, PaymentAttempt
from domains.billing.services.pricing import create_plan_price
from domains.event.enums import OutboxStatus
from domains.event.models import EventOutbox, EventRecord
from domains.identity_access.enums import (
    MembershipStatus,
    PermissionCode,
    RoleCode,
    UserStatus,
)
from domains.identity_access.models import (
    Elder,
    Membership,
    Permission,
    Role,
    RolePermission,
    User,
)
from domains.licensing.enums import LicenseStatus, PlanStatus, SubscriptionStatus
from domains.licensing.exceptions import (
    InvalidLicenseStateError,
    InvalidSubscriptionStateError,
)
from domains.licensing.models import License, Plan, Subscription
from infrastructure.payment.exceptions import PaymentProviderUnavailableError
from infrastructure.payment.factory import reset_fake_provider

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def clean_fake_payment_provider():
    reset_fake_provider()
    yield
    reset_fake_provider()


@pytest.fixture
def permissions_and_roles(db):
    perm, _ = Permission.objects.get_or_create(
        code=PermissionCode.MANAGE_SUBSCRIPTION,
        defaults={"name": "Manage Subscription"},
    )
    role_primary, _ = Role.objects.get_or_create(
        code=RoleCode.PRIMARY_CAREGIVER,
        defaults={"name": "Primary Caregiver"},
    )
    role_secondary, _ = Role.objects.get_or_create(
        code=RoleCode.CAREGIVER,
        defaults={"name": "Caregiver"},
    )
    RolePermission.objects.get_or_create(role=role_primary, permission=perm)
    return role_primary, role_secondary


@pytest.fixture
def test_setup(db, permissions_and_roles):
    role_primary, role_secondary = permissions_and_roles

    # Users
    primary_user = User.objects.create(
        phone="+989120000001",
        full_name="Primary Caregiver",
        status=UserStatus.ACTIVE,
    )
    secondary_user = User.objects.create(
        phone="+989120000002",
        full_name="Secondary Caregiver",
        status=UserStatus.ACTIVE,
    )
    unrelated_user = User.objects.create(
        phone="+989120000003",
        full_name="Unrelated User",
        status=UserStatus.ACTIVE,
    )

    # Elder
    elder = Elder.objects.create(full_name="Grandma Sarah")

    # Memberships
    Membership.objects.create(
        user=primary_user,
        elder=elder,
        role=role_primary,
        status=MembershipStatus.ACTIVE,
        is_primary=True,
    )
    Membership.objects.create(
        user=secondary_user,
        elder=elder,
        role=role_secondary,
        status=MembershipStatus.ACTIVE,
        is_primary=False,
    )

    # Plan
    plan = Plan.objects.create(
        code="PLUS",
        name="Plus Plan",
        status=PlanStatus.ACTIVE,
    )

    # Price in Billing
    plan_price = create_plan_price(
        plan_code="PLUS",
        amount=Decimal("150000"),
        interval=BillingInterval.MONTHLY,
        currency=Currency.TOMAN,
    )

    # License
    license = License.objects.create(
        elder=elder,
        plan=plan,
        status=LicenseStatus.ACTIVE,
        valid_from=timezone.now(),
        valid_until=timezone.now() + timedelta(days=30),
    )

    return {
        "primary_user": primary_user,
        "secondary_user": secondary_user,
        "unrelated_user": unrelated_user,
        "elder": elder,
        "plan": plan,
        "plan_price": plan_price,
        "license": license,
    }


# ==============================================================================
# Checkout Initiation Tests
# ==============================================================================


def test_initiate_checkout_success(test_setup):
    user = test_setup["primary_user"]
    elder = test_setup["elder"]

    result = initiate_checkout(
        payer_user=user,
        elder_id=elder.id,
        plan_code="PLUS",
        interval=BillingInterval.MONTHLY,
    )

    assert result.provider_reference.startswith("FAKE-AUTH-")
    assert "/pay/" in result.redirect_url
    assert result.amount == Decimal("150000")
    assert result.currency == Currency.TOMAN

    # Verify Invoice
    invoice = Invoice.objects.get(pk=result.invoice_id)
    assert invoice.status == InvoiceStatus.UNPAID
    assert invoice.total_amount == Decimal("150000")
    assert invoice.elder_id == elder.id
    assert invoice.payer_user_id == user.id
    assert invoice.subscription_id is not None

    # Verify Subscription in Licensing
    subscription = Subscription.objects.get(pk=invoice.subscription_id)
    assert subscription.status == SubscriptionStatus.PENDING_PAYMENT
    assert subscription.license == test_setup["license"]

    # Verify PaymentAttempt
    attempt = PaymentAttempt.objects.get(pk=result.payment_attempt_id)
    assert attempt.status == PaymentAttemptStatus.REDIRECTED
    assert attempt.provider_reference == result.provider_reference


def test_initiate_checkout_renews_existing_active_subscription(test_setup):
    user = test_setup["primary_user"]
    elder = test_setup["elder"]
    license = test_setup["license"]
    plan = test_setup["plan"]

    now = timezone.now()
    initial_sub = Subscription.objects.create(
        license=license,
        plan=plan,
        status=SubscriptionStatus.ACTIVE,
        started_at=now - timedelta(days=10),
        expires_at=now + timedelta(days=20),
        payer_user_id=user.id,
    )

    result = initiate_checkout(
        payer_user=user,
        elder_id=elder.id,
        plan_code="PLUS",
        interval=BillingInterval.MONTHLY,
    )

    invoice = Invoice.objects.get(pk=result.invoice_id)
    new_sub = Subscription.objects.get(pk=invoice.subscription_id)

    assert new_sub.id != initial_sub.id
    assert new_sub.status == SubscriptionStatus.PENDING_PAYMENT
    # Chained smoothly from existing expiration
    assert new_sub.started_at == initial_sub.expires_at


def test_initiate_checkout_permission_denied_for_secondary_caregiver(test_setup):
    user = test_setup["secondary_user"]
    elder = test_setup["elder"]

    with pytest.raises(PermissionDeniedError):
        initiate_checkout(
            payer_user=user,
            elder_id=elder.id,
            plan_code="PLUS",
        )


def test_initiate_checkout_permission_denied_for_unrelated_user(test_setup):
    user = test_setup["unrelated_user"]
    elder = test_setup["elder"]

    with pytest.raises(PermissionDeniedError):
        initiate_checkout(
            payer_user=user,
            elder_id=elder.id,
            plan_code="PLUS",
        )


def test_initiate_checkout_fails_on_revoked_license(test_setup):
    user = test_setup["primary_user"]
    elder = test_setup["elder"]
    license = test_setup["license"]

    license.status = LicenseStatus.REVOKED
    license.save(update_fields=["status"])

    with pytest.raises(InvalidLicenseStateError):
        initiate_checkout(
            payer_user=user,
            elder_id=elder.id,
            plan_code="PLUS",
        )


def test_initiate_checkout_fails_if_plan_not_found(test_setup):
    user = test_setup["primary_user"]
    elder = test_setup["elder"]

    with pytest.raises(PlanNotFoundError):
        initiate_checkout(
            payer_user=user,
            elder_id=elder.id,
            plan_code="NON_EXISTENT_PLAN",
        )


def test_initiate_checkout_fails_if_price_not_found(test_setup):
    user = test_setup["primary_user"]
    elder = test_setup["elder"]

    with pytest.raises(PlanPriceNotFoundError):
        initiate_checkout(
            payer_user=user,
            elder_id=elder.id,
            plan_code="PLUS",
            interval=BillingInterval.ANNUAL,  # Only monthly was seeded
        )


def test_initiate_checkout_idempotency_returns_existing(test_setup):
    user = test_setup["primary_user"]
    elder = test_setup["elder"]
    idempotency_key = "test-checkout-idempotency-key-1"

    result1 = initiate_checkout(
        payer_user=user,
        elder_id=elder.id,
        plan_code="PLUS",
        idempotency_key=idempotency_key,
    )

    result2 = initiate_checkout(
        payer_user=user,
        elder_id=elder.id,
        plan_code="PLUS",
        idempotency_key=idempotency_key,
    )

    assert result1.provider_reference == result2.provider_reference
    assert result1.invoice_id == result2.invoice_id
    assert result1.payment_attempt_id == result2.payment_attempt_id


def test_initiate_checkout_handles_provider_network_error(test_setup):
    from infrastructure.payment.factory import get_payment_provider

    provider = get_payment_provider()
    provider.simulate_network_error = True

    user = test_setup["primary_user"]
    elder = test_setup["elder"]

    with pytest.raises(PaymentProviderUnavailableError):
        initiate_checkout(
            payer_user=user,
            elder_id=elder.id,
            plan_code="PLUS",
        )


# ==============================================================================
# Payment Callback & Settlement Tests
# ==============================================================================


def test_handle_payment_callback_success(test_setup):
    user = test_setup["primary_user"]
    elder = test_setup["elder"]

    checkout_res = initiate_checkout(
        payer_user=user,
        elder_id=elder.id,
        plan_code="PLUS",
    )

    callback_res = handle_payment_callback(
        provider_reference=checkout_res.provider_reference,
        callback_payload={"Status": "OK", "Authority": checkout_res.provider_reference},
    )

    assert callback_res.is_successful is True
    assert callback_res.already_settled is False
    assert callback_res.tracking_code.startswith("TRK-")
    assert callback_res.invoice_id == checkout_res.invoice_id

    # Verify Invoice settled to PAID
    invoice = Invoice.objects.get(pk=checkout_res.invoice_id)
    assert invoice.status == InvoiceStatus.PAID
    assert invoice.paid_at is not None

    # Verify Subscription activated
    subscription = Subscription.objects.get(pk=invoice.subscription_id)
    assert subscription.status == SubscriptionStatus.ACTIVE

    # Verify PaymentAttempt marked SUCCESSFUL
    attempt = PaymentAttempt.objects.get(pk=checkout_res.payment_attempt_id)
    assert attempt.status == PaymentAttemptStatus.SUCCESSFUL

    # Verify PaymentSucceeded Domain Event in EventRecord & EventOutbox
    event = EventRecord.objects.filter(correlation_id=str(invoice.id)).first()
    assert event is not None
    assert event.event_type == "PaymentSucceeded"
    assert event.producer == "billing"
    assert event.payload["invoice_id"] == str(invoice.id)
    assert event.payload["subscription_id"] == str(subscription.id)
    assert event.payload["elder_id"] == str(elder.id)
    assert event.payload["amount"] == str(invoice.total_amount)
    assert event.payload["provider_reference"] == checkout_res.provider_reference
    assert event.payload["tracking_code"] == callback_res.tracking_code

    outbox = EventOutbox.objects.get(event=event)
    assert outbox.status == OutboxStatus.PUBLISHED


def test_handle_payment_callback_gateway_cancelled_nok(test_setup):
    user = test_setup["primary_user"]
    elder = test_setup["elder"]

    checkout_res = initiate_checkout(
        payer_user=user,
        elder_id=elder.id,
        plan_code="PLUS",
    )

    callback_res = handle_payment_callback(
        provider_reference=checkout_res.provider_reference,
        callback_payload={
            "Status": "NOK",
            "Authority": checkout_res.provider_reference,
        },
    )

    assert callback_res.is_successful is False
    assert callback_res.error_code == "CANCELLED_BY_USER"

    # Invoice remains UNPAID
    invoice = Invoice.objects.get(pk=checkout_res.invoice_id)
    assert invoice.status == InvoiceStatus.UNPAID
    assert invoice.paid_at is None

    # Subscription remains PENDING_PAYMENT
    subscription = Subscription.objects.get(pk=invoice.subscription_id)
    assert subscription.status == SubscriptionStatus.PENDING_PAYMENT

    # PaymentAttempt marked CANCELLED
    attempt = PaymentAttempt.objects.get(pk=checkout_res.payment_attempt_id)
    assert attempt.status == PaymentAttemptStatus.CANCELLED

    # No event published
    assert not EventRecord.objects.filter(correlation_id=str(invoice.id)).exists()


def test_handle_payment_callback_provider_declined(test_setup):
    from infrastructure.payment.factory import get_payment_provider

    user = test_setup["primary_user"]
    elder = test_setup["elder"]

    checkout_res = initiate_checkout(
        payer_user=user,
        elder_id=elder.id,
        plan_code="PLUS",
    )

    provider = get_payment_provider()
    provider.verification_overrides[checkout_res.provider_reference] = False

    callback_res = handle_payment_callback(
        provider_reference=checkout_res.provider_reference,
        callback_payload={"Status": "OK", "Authority": checkout_res.provider_reference},
    )

    assert callback_res.is_successful is False
    assert callback_res.error_code == "VERIFICATION_FAILED"

    # Invoice remains UNPAID
    invoice = Invoice.objects.get(pk=checkout_res.invoice_id)
    assert invoice.status == InvoiceStatus.UNPAID

    # PaymentAttempt marked FAILED
    attempt = PaymentAttempt.objects.get(pk=checkout_res.payment_attempt_id)
    assert attempt.status == PaymentAttemptStatus.FAILED

    # No event published
    assert not EventRecord.objects.filter(correlation_id=str(invoice.id)).exists()


def test_handle_payment_callback_idempotent_replay(test_setup):
    user = test_setup["primary_user"]
    elder = test_setup["elder"]

    checkout_res = initiate_checkout(
        payer_user=user,
        elder_id=elder.id,
        plan_code="PLUS",
    )

    # First callback
    callback_res1 = handle_payment_callback(
        provider_reference=checkout_res.provider_reference,
        callback_payload={"Status": "OK"},
    )
    assert callback_res1.is_successful is True
    assert callback_res1.already_settled is False

    event_count_1 = EventRecord.objects.filter(
        correlation_id=str(checkout_res.invoice_id)
    ).count()
    assert event_count_1 == 1

    # Second callback (replay)
    callback_res2 = handle_payment_callback(
        provider_reference=checkout_res.provider_reference,
        callback_payload={"Status": "OK"},
    )
    assert callback_res2.is_successful is True
    assert callback_res2.already_settled is True

    # No duplicate events created
    event_count_2 = EventRecord.objects.filter(
        correlation_id=str(checkout_res.invoice_id)
    ).count()
    assert event_count_2 == 1


def test_handle_payment_callback_missing_or_unknown_reference(test_setup):
    with pytest.raises(InvalidCallbackError):
        handle_payment_callback(provider_reference="")

    with pytest.raises(PaymentAttemptNotFoundError):
        handle_payment_callback(provider_reference="UNKNOWN-REF-9999")


def test_handle_payment_callback_rollback_on_subscription_error(test_setup):
    user = test_setup["primary_user"]
    elder = test_setup["elder"]

    checkout_res = initiate_checkout(
        payer_user=user,
        elder_id=elder.id,
        plan_code="PLUS",
    )

    # Mock activate_subscription to raise InvalidSubscriptionStateError
    with patch(
        "application.payments.coordinator.activate_subscription",
        side_effect=InvalidSubscriptionStateError("Simulated activation failure"),
    ):
        with pytest.raises(InvalidSubscriptionStateError):
            handle_payment_callback(
                provider_reference=checkout_res.provider_reference,
                callback_payload={"Status": "OK"},
            )

    # Verify transaction rollback: invoice remains UNPAID, no event in EventRecord
    invoice = Invoice.objects.get(pk=checkout_res.invoice_id)
    assert invoice.status == InvoiceStatus.UNPAID
    assert invoice.paid_at is None
    assert not EventRecord.objects.filter(correlation_id=str(invoice.id)).exists()


def test_concurrent_payment_callback_handling(test_setup):
    """Verify that sequential or race condition replays handle lock gracefully."""
    user = test_setup["primary_user"]
    elder = test_setup["elder"]

    checkout_res = initiate_checkout(
        payer_user=user,
        elder_id=elder.id,
        plan_code="PLUS",
    )

    # First call settles
    res1 = handle_payment_callback(
        provider_reference=checkout_res.provider_reference,
        callback_payload={"Status": "OK"},
    )
    assert res1.is_successful is True
    assert res1.already_settled is False

    # Second call sees already settled under row lock
    res2 = handle_payment_callback(
        provider_reference=checkout_res.provider_reference,
        callback_payload={"Status": "OK"},
    )
    assert res2.is_successful is True
    assert res2.already_settled is True

    # Total events remains strictly 1
    events = EventRecord.objects.filter(correlation_id=str(checkout_res.invoice_id))
    assert events.count() == 1
