"""Subscription lifecycle operations supporting License."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone

from domains.licensing.enums import LicenseStatus, PlanStatus, SubscriptionStatus
from domains.licensing.exceptions import (
    InvalidLicenseStateError,
    InvalidSubscriptionStateError,
    SubscriptionNotFoundError,
)
from domains.licensing.models import License, Plan, Subscription
from domains.licensing.services.licenses import change_license_plan


def get_subscription(subscription_id: uuid.UUID) -> Subscription:
    try:
        return Subscription.objects.select_related("license", "plan").get(pk=subscription_id)
    except Subscription.DoesNotExist as exc:
        raise SubscriptionNotFoundError(f"Subscription {subscription_id} not found.") from exc


def get_active_subscription_for_license(license_id: uuid.UUID) -> Subscription | None:
    now = timezone.now()
    return (
        Subscription.objects.filter(
            license_id=license_id,
            status=SubscriptionStatus.ACTIVE,
            started_at__lte=now,
            expires_at__gt=now,
        )
        .select_related("plan")
        .order_by("-expires_at")
        .first()
    )


@transaction.atomic
def initiate_subscription(
    *,
    license_id: uuid.UUID,
    plan_code: str,
    duration: timedelta | None = None,
    started_at: datetime | None = None,
    expires_at: datetime | None = None,
    auto_renew: bool = False,
    is_trial: bool = False,
    payer_user_id: uuid.UUID | None = None,
    initial_status: SubscriptionStatus = SubscriptionStatus.PENDING_PAYMENT,
) -> Subscription:
    """Initiate a commercial subscription supporting an existing License."""
    try:
        license = License.objects.select_for_update().get(pk=license_id)
    except License.DoesNotExist as exc:
        raise InvalidLicenseStateError(f"License {license_id} does not exist.") from exc

    if license.status == LicenseStatus.REVOKED:
        raise InvalidLicenseStateError("Cannot initiate subscription on a revoked license.")

    plan = Plan.objects.get(code=plan_code, status=PlanStatus.ACTIVE)

    start_time = started_at or timezone.now()
    if expires_at is not None:
        end_time = expires_at
    elif duration is not None:
        end_time = start_time + duration
    else:
        # Default standard 30-day period
        end_time = start_time + timedelta(days=30)

    if end_time <= start_time:
        raise InvalidSubscriptionStateError("Subscription expiration must be strictly after start time.")

    return Subscription.objects.create(
        license=license,
        plan=plan,
        status=initial_status,
        started_at=start_time,
        expires_at=end_time,
        auto_renew=auto_renew,
        is_trial=is_trial,
        payer_user_id=payer_user_id,
    )


@transaction.atomic
def activate_subscription(*, subscription_id: uuid.UUID) -> Subscription:
    """Activate a pending or past-due subscription upon payment settlement.

    Extends the associated License's valid_until window and ensures status is ACTIVE.
    """
    subscription = (
        Subscription.objects.select_for_update()
        .select_related("license", "plan")
        .filter(pk=subscription_id)
        .first()
    )
    if subscription is None:
        raise SubscriptionNotFoundError(f"Subscription {subscription_id} not found.")

    if subscription.status == SubscriptionStatus.ACTIVE:
        return subscription

    if subscription.status not in {
        SubscriptionStatus.PENDING_PAYMENT,
        SubscriptionStatus.PAST_DUE,
    }:
        raise InvalidSubscriptionStateError(
            f"Cannot activate subscription with status '{subscription.status}'."
        )

    subscription.status = SubscriptionStatus.ACTIVE
    subscription.save(update_fields=["status"])

    # Synchronize License
    license = subscription.license
    if license.plan_id != subscription.plan_id:
        change_license_plan(license_id=license.id, plan_code=subscription.plan.code)
        license.refresh_from_db()

    # Extend license validity window
    if license.valid_until is None or license.valid_until < subscription.expires_at:
        license.valid_until = subscription.expires_at

    if license.status != LicenseStatus.ACTIVE:
        license.status = LicenseStatus.ACTIVE

    license.save(update_fields=["valid_until", "status"])
    return subscription


@transaction.atomic
def renew_subscription(
    *,
    subscription_id: uuid.UUID,
    duration: timedelta | None = None,
    plan_code: str | None = None,
    auto_renew: bool | None = None,
    payer_user_id: uuid.UUID | None = None,
) -> Subscription:
    """Create a new sequential subscription for an existing subscription.

    Preserves prepaid time: starts at current subscription's expires_at if in the future,
    or now if the current subscription has already lapsed.
    """
    current_sub = (
        Subscription.objects.select_for_update()
        .select_related("license", "plan")
        .filter(pk=subscription_id)
        .first()
    )
    if current_sub is None:
        raise SubscriptionNotFoundError(f"Subscription {subscription_id} not found.")

    if current_sub.license.status == LicenseStatus.REVOKED:
        raise InvalidLicenseStateError("Cannot renew subscription on a revoked license.")

    target_plan_code = plan_code or current_sub.plan.code
    target_plan = Plan.objects.get(code=target_plan_code, status=PlanStatus.ACTIVE)

    now = timezone.now()
    # Chaining: If current subscription is still active/in future, new start is its expiry
    new_start = current_sub.expires_at if current_sub.expires_at > now else now
    sub_duration = duration or timedelta(days=30)
    new_end = new_start + sub_duration

    return Subscription.objects.create(
        license=current_sub.license,
        plan=target_plan,
        status=SubscriptionStatus.PENDING_PAYMENT,
        started_at=new_start,
        expires_at=new_end,
        auto_renew=current_sub.auto_renew if auto_renew is None else auto_renew,
        is_trial=False,
        payer_user_id=payer_user_id or current_sub.payer_user_id,
    )


@transaction.atomic
def cancel_subscription(*, subscription_id: uuid.UUID) -> Subscription:
    """Cancel subscription auto-renewal.

    Preserves current active term until expiration unless term has not started.
    """
    subscription = Subscription.objects.select_for_update().get(pk=subscription_id)
    subscription.auto_renew = False

    now = timezone.now()
    if subscription.status == SubscriptionStatus.PENDING_PAYMENT or subscription.started_at > now:
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.save(update_fields=["auto_renew", "status"])
    else:
        subscription.save(update_fields=["auto_renew"])

    return subscription


@transaction.atomic
def expire_subscription(*, subscription_id: uuid.UUID) -> Subscription:
    """Transition subscription to EXPIRED status."""
    subscription = Subscription.objects.select_for_update().get(pk=subscription_id)
    if subscription.status == SubscriptionStatus.EXPIRED:
        return subscription

    subscription.status = SubscriptionStatus.EXPIRED
    subscription.save(update_fields=["status"])
    return subscription
