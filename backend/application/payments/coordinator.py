"""Application-level Payment Coordinator.

Implements ADR-016 architectural exception coordinating Billing and Licensing
during payment settlement for immediate UX while decoupling via Domain Events.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.db import transaction

from application.payments.events import publish_payment_succeeded_event
from application.payments.exceptions import (
    ElderNotFoundError,
    InvalidCallbackError,
    PaymentAttemptNotFoundError,
    PaymentCoordinatorError,
    PermissionDeniedError,
    PlanNotFoundError,
    PlanPriceNotFoundError,
)
from domains.billing.enums import (
    BillingInterval,
    Currency,
    InvoiceStatus,
    PaymentAttemptStatus,
    PaymentProviderType,
)
from domains.billing.models import Invoice, PaymentAttempt
from domains.billing.services.invoices import create_invoice, settle_invoice
from domains.billing.services.payments import (
    get_payment_attempt_by_idempotency_key,
    get_payment_attempt_by_provider_reference,
    record_payment_attempt,
    update_payment_attempt_status,
)
from domains.billing.services.pricing import get_active_price
from domains.identity_access.enums import PermissionCode
from domains.identity_access.models import Elder, User
from domains.identity_access.services.authorization import can
from domains.licensing.enums import LicenseStatus, PlanStatus
from domains.licensing.exceptions import InvalidLicenseStateError
from domains.licensing.models import License, Plan
from domains.licensing.services.subscriptions import (
    activate_subscription,
    get_active_subscription_for_license,
    initiate_subscription,
    renew_subscription,
)
from infrastructure.payment.factory import get_payment_provider
from infrastructure.payment.ports import PaymentRequest

logger = logging.getLogger("yara.payments.coordinator")


@dataclass(frozen=True)
class CheckoutResult:
    """Normalized response from initiating a checkout flow."""

    provider_reference: str
    redirect_url: str
    invoice_id: uuid.UUID
    payment_attempt_id: uuid.UUID
    amount: Decimal
    currency: str


@dataclass(frozen=True)
class PaymentCallbackResult:
    """Normalized response from processing a gateway callback."""

    is_successful: bool
    invoice_id: uuid.UUID | None
    provider_reference: str
    tracking_code: str = ""
    amount_paid: Decimal | None = None
    error_code: str = ""
    error_message: str = ""
    already_settled: bool = False


def initiate_checkout(
    *,
    payer_user: User,
    elder_id: uuid.UUID,
    plan_code: str,
    interval: str = BillingInterval.MONTHLY,
    currency: str = Currency.TOMAN,
    callback_url: str | None = None,
    idempotency_key: str | None = None,
    payer_mobile: str | None = None,
    payer_email: str | None = None,
) -> CheckoutResult:
    """Initiate checkout flow for an Elder subscription.

    Validates permissions, resolves authoritative price, sets up subscription,
    creates billing invoice, records payment attempt, and requests gateway redirect.
    """
    try:
        elder = Elder.objects.get(pk=elder_id)
    except Elder.DoesNotExist as exc:
        raise ElderNotFoundError(f"Elder {elder_id} not found.") from exc

    if not can(payer_user, PermissionCode.MANAGE_SUBSCRIPTION, elder):
        raise PermissionDeniedError(
            f"User {payer_user.id} lacks MANAGE_SUBSCRIPTION permission for Elder {elder_id}."
        )

    license = License.objects.filter(
        elder_id=elder_id, status=LicenseStatus.ACTIVE
    ).first()
    if license is None:
        raise InvalidLicenseStateError(f"No active license found for Elder {elder_id}.")

    plan = Plan.objects.filter(code=plan_code, status=PlanStatus.ACTIVE).first()
    if plan is None:
        raise PlanNotFoundError(f"Plan '{plan_code}' not found or is inactive.")

    price = get_active_price(plan_code=plan_code, interval=interval, currency=currency)
    if price is None:
        raise PlanPriceNotFoundError(
            f"No active price found for plan '{plan_code}', interval '{interval}', currency '{currency}'."
        )

    # Idempotency check: if an attempt already exists with this key, return existing result
    if idempotency_key:
        existing_attempt = get_payment_attempt_by_idempotency_key(idempotency_key)
        if existing_attempt is not None:
            if existing_attempt.status == PaymentAttemptStatus.SUCCESSFUL:
                raise PaymentCoordinatorError(
                    "Payment attempt with this idempotency key already succeeded."
                )
            if existing_attempt.provider_reference:
                redirect_url = ""
                if (
                    existing_attempt.raw_payload
                    and "redirect_url" in existing_attempt.raw_payload
                ):
                    redirect_url = existing_attempt.raw_payload["redirect_url"]
                return CheckoutResult(
                    provider_reference=existing_attempt.provider_reference,
                    redirect_url=redirect_url,
                    invoice_id=existing_attempt.invoice_id,
                    payment_attempt_id=existing_attempt.id,
                    amount=existing_attempt.amount,
                    currency=existing_attempt.invoice.currency,
                )

    # Determine duration
    duration = (
        timedelta(days=365)
        if interval == BillingInterval.ANNUAL
        else timedelta(days=30)
    )

    # Setup subscription in Licensing domain
    active_sub = get_active_subscription_for_license(license.id)
    if active_sub is not None:
        subscription = renew_subscription(
            subscription_id=active_sub.id,
            duration=duration,
            plan_code=plan_code,
            payer_user_id=payer_user.id,
        )
    else:
        subscription = initiate_subscription(
            license_id=license.id,
            plan_code=plan_code,
            duration=duration,
            payer_user_id=payer_user.id,
        )

    # Create Invoice in Billing domain (authoritative price)
    invoice = create_invoice(
        elder_id=elder_id,
        payer_user_id=payer_user.id,
        subscription_id=subscription.id,
        currency=price.currency,
        line_items_data=[
            {
                "description": f"Subscription {plan.name} ({interval})",
                "amount": price.amount,
                "quantity": 1,
                "line_type": "SUBSCRIPTION",
            }
        ],
    )

    # Record PaymentAttempt in Billing domain
    effective_idempotency_key = (
        idempotency_key or f"checkout:{invoice.id}:{uuid.uuid4()}"
    )
    configured_provider = getattr(settings, "PAYMENT_PROVIDER", "fake").upper()
    provider_enum = (
        PaymentProviderType.ZARINPAL
        if configured_provider == "ZARINPAL"
        else PaymentProviderType.FAKE
    )

    attempt = record_payment_attempt(
        invoice_id=invoice.id,
        provider=provider_enum,
        idempotency_key=effective_idempotency_key,
        amount=invoice.total_amount,
    )

    # Call Payment Provider Port
    effective_callback = callback_url or getattr(
        settings,
        "ZARINPAL_CALLBACK_URL",
        "https://api.yara.care/api/v1/payments/verify/",
    )

    provider = get_payment_provider()
    payment_req = PaymentRequest(
        invoice_id=invoice.id,
        amount=invoice.total_amount,
        currency=invoice.currency,
        callback_url=effective_callback,
        description=f"Yara Care Subscription - {plan.name}",
        payer_mobile=payer_mobile,
        payer_email=payer_email,
        metadata={
            "elder_id": str(elder_id),
            "subscription_id": str(subscription.id),
            "payment_attempt_id": str(attempt.id),
        },
    )

    req_result = provider.request_payment(payment_req)

    update_payment_attempt_status(
        attempt_id=attempt.id,
        status=PaymentAttemptStatus.REDIRECTED,
        provider_reference=req_result.provider_reference,
        raw_payload={
            **req_result.raw_response,
            "redirect_url": req_result.redirect_url,
        },
    )

    return CheckoutResult(
        provider_reference=req_result.provider_reference,
        redirect_url=req_result.redirect_url,
        invoice_id=invoice.id,
        payment_attempt_id=attempt.id,
        amount=invoice.total_amount,
        currency=invoice.currency,
    )


def handle_payment_callback(
    *,
    provider_reference: str,
    callback_payload: dict[str, Any] | None = None,
) -> PaymentCallbackResult:
    """Handle gateway return callback.

    Correlates payment attempt, verifies payment server-to-server with provider,
    and atomically settles invoice, activates subscription, and publishes domain event.
    """
    clean_ref = (provider_reference or "").strip()
    if not clean_ref:
        raise InvalidCallbackError("Missing provider reference in callback.")

    attempt = get_payment_attempt_by_provider_reference(clean_ref)
    if attempt is None:
        raise PaymentAttemptNotFoundError(
            f"No payment attempt found for provider reference '{clean_ref}'."
        )

    invoice = attempt.invoice

    # 1. Early idempotency check: already settled?
    if (
        invoice.status == InvoiceStatus.PAID
        and attempt.status == PaymentAttemptStatus.SUCCESSFUL
    ):
        tracking_code = (
            attempt.raw_payload.get("tracking_code", "") if attempt.raw_payload else ""
        )
        return PaymentCallbackResult(
            is_successful=True,
            invoice_id=invoice.id,
            provider_reference=clean_ref,
            tracking_code=tracking_code,
            amount_paid=attempt.amount,
            already_settled=True,
        )

    # 2. Gateway cancellation check (e.g. Status=NOK)
    if callback_payload and str(callback_payload.get("Status", "")).upper() == "NOK":
        update_payment_attempt_status(
            attempt_id=attempt.id,
            status=PaymentAttemptStatus.CANCELLED,
            raw_payload=callback_payload,
        )
        return PaymentCallbackResult(
            is_successful=False,
            invoice_id=invoice.id,
            provider_reference=clean_ref,
            error_code="CANCELLED_BY_USER",
            error_message="Payment was cancelled or declined at gateway return.",
        )

    # 3. Provider verification (EXECUTED OUTSIDE DATABASE LOCK)
    provider = get_payment_provider()
    verify_result = provider.verify_payment(
        provider_reference=clean_ref,
        amount=attempt.amount,
        currency=invoice.currency,
        callback_payload=callback_payload,
    )

    if not verify_result.is_successful:
        update_payment_attempt_status(
            attempt_id=attempt.id,
            status=PaymentAttemptStatus.FAILED,
            raw_payload=verify_result.raw_response,
        )
        return PaymentCallbackResult(
            is_successful=False,
            invoice_id=invoice.id,
            provider_reference=clean_ref,
            error_code=verify_result.error_code,
            error_message=verify_result.error_message,
        )

    # 4. Atomic settlement under database lock
    with transaction.atomic():
        locked_invoice = Invoice.objects.select_for_update().get(pk=invoice.id)
        locked_attempt = PaymentAttempt.objects.select_for_update().get(pk=attempt.id)

        # Concurrency re-check under lock
        if locked_invoice.status == InvoiceStatus.PAID:
            return PaymentCallbackResult(
                is_successful=True,
                invoice_id=locked_invoice.id,
                provider_reference=clean_ref,
                tracking_code=verify_result.tracking_code,
                amount_paid=verify_result.amount_paid or locked_invoice.total_amount,
                already_settled=True,
            )

        # Mark attempt successful
        update_payment_attempt_status(
            attempt_id=locked_attempt.id,
            status=PaymentAttemptStatus.SUCCESSFUL,
            raw_payload={
                **verify_result.raw_response,
                "tracking_code": verify_result.tracking_code,
                "card_pan_masked": verify_result.card_pan_masked,
            },
        )

        # Settle invoice
        settle_invoice(invoice_id=locked_invoice.id)

        # Activate subscription
        if locked_invoice.subscription_id:
            activate_subscription(subscription_id=locked_invoice.subscription_id)

        # Publish PaymentSucceeded domain event to Transactional Outbox
        publish_payment_succeeded_event(
            invoice=locked_invoice,
            provider_reference=clean_ref,
            tracking_code=verify_result.tracking_code,
            amount=verify_result.amount_paid or locked_invoice.total_amount,
            currency=locked_invoice.currency,
        )

    return PaymentCallbackResult(
        is_successful=True,
        invoice_id=locked_invoice.id,
        provider_reference=clean_ref,
        tracking_code=verify_result.tracking_code,
        amount_paid=verify_result.amount_paid or locked_invoice.total_amount,
        already_settled=False,
    )
