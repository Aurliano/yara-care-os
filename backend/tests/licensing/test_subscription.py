"""Tests for Subscription aggregate lifecycle and License integration."""

import uuid
from datetime import timedelta
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from domains.identity_access.services.profiles import create_elder
from domains.licensing.enums import EntitlementKey, LicenseStatus, SubscriptionStatus
from domains.licensing.exceptions import (
    InvalidLicenseStateError,
    InvalidSubscriptionStateError,
    SubscriptionNotFoundError,
)
from domains.licensing.models import License, LicensePlanHistory, Plan, Subscription
from domains.licensing.services.entitlements import can_use_feature, get_limit
from domains.licensing.services.licenses import activate_license, revoke_license
from domains.licensing.services.subscriptions import (
    activate_subscription,
    cancel_subscription,
    expire_subscription,
    get_active_subscription_for_license,
    get_subscription,
    initiate_subscription,
    renew_subscription,
)


@pytest.mark.django_db
def test_subscription_initiation_and_binding(elder):
    license = activate_license(
        elder_id=elder.id,
        plan_code="BASIC",
        valid_from=timezone.now() - timedelta(days=1),
    )
    sub = initiate_subscription(
        license_id=license.id,
        plan_code="PLUS",
        duration=timedelta(days=30),
        payer_user_id=uuid.uuid4(),
    )
    assert sub.status == SubscriptionStatus.PENDING_PAYMENT
    assert sub.license_id == license.id
    assert sub.plan.code == "PLUS"
    assert sub.expires_at > sub.started_at
    assert sub.is_trial is False


@pytest.mark.django_db
def test_subscription_activation_extends_license_and_updates_plan(elder):
    now = timezone.now()
    license = activate_license(
        elder_id=elder.id,
        plan_code="BASIC",
        valid_from=now - timedelta(days=1),
        valid_until=now + timedelta(days=5),
    )
    target_end = now + timedelta(days=35)
    sub = initiate_subscription(
        license_id=license.id,
        plan_code="PREMIUM",
        started_at=now,
        expires_at=target_end,
    )
    activated_sub = activate_subscription(subscription_id=sub.id)
    assert activated_sub.status == SubscriptionStatus.ACTIVE

    license.refresh_from_db()
    assert license.status == LicenseStatus.ACTIVE
    assert license.plan.code == "PREMIUM"
    assert license.valid_until == target_end

    # Verify audit history
    history = LicensePlanHistory.objects.filter(license=license).first()
    assert history is not None
    assert history.previous_plan.code == "BASIC"
    assert history.new_plan.code == "PREMIUM"

    # Verify entitlements reflected immediately
    assert can_use_feature(elder.id, EntitlementKey.VIDEO_CALL) is True
    assert get_limit(elder.id, EntitlementKey.MAX_CAREGIVERS) == 10


@pytest.mark.django_db
def test_arbitrary_duration_support_trials_and_rentals(elder):
    license = activate_license(
        elder_id=elder.id,
        plan_code="BASIC",
        valid_from=timezone.now(),
    )

    # 1. 14-day free trial
    trial_sub = initiate_subscription(
        license_id=license.id,
        plan_code="PLUS",
        duration=timedelta(days=14),
        is_trial=True,
    )
    assert trial_sub.is_trial is True
    assert (trial_sub.expires_at - trial_sub.started_at).days == 14

    # 2. 7-day short-term post-op Hub rental
    rental_sub = initiate_subscription(
        license_id=license.id,
        plan_code="PLUS",
        duration=timedelta(days=7),
    )
    assert (rental_sub.expires_at - rental_sub.started_at).days == 7

    # 3. 365-day annual subscription
    annual_sub = initiate_subscription(
        license_id=license.id,
        plan_code="PREMIUM",
        duration=timedelta(days=365),
        auto_renew=True,
    )
    assert (annual_sub.expires_at - annual_sub.started_at).days == 365
    assert annual_sub.auto_renew is True


@pytest.mark.django_db
def test_subscription_cancellation(elder):
    license = activate_license(
        elder_id=elder.id,
        plan_code="BASIC",
        valid_from=timezone.now(),
    )
    sub = initiate_subscription(
        license_id=license.id,
        plan_code="PLUS",
        duration=timedelta(days=30),
        auto_renew=True,
    )
    activate_subscription(subscription_id=sub.id)

    # Cancelling an active subscription turns off auto_renew, preserving active term
    cancelled = cancel_subscription(subscription_id=sub.id)
    assert cancelled.auto_renew is False
    assert cancelled.status == SubscriptionStatus.ACTIVE


@pytest.mark.django_db
def test_subscription_expiration(elder):
    license = activate_license(
        elder_id=elder.id,
        plan_code="BASIC",
        valid_from=timezone.now(),
    )
    sub = initiate_subscription(
        license_id=license.id,
        plan_code="PLUS",
        duration=timedelta(days=30),
    )
    activate_subscription(subscription_id=sub.id)

    expired = expire_subscription(subscription_id=sub.id)
    assert expired.status == SubscriptionStatus.EXPIRED


@pytest.mark.django_db
def test_subscription_validation_rules(elder):
    license = activate_license(
        elder_id=elder.id,
        plan_code="BASIC",
        valid_from=timezone.now(),
    )
    now = timezone.now()

    # Invalid end time before start time via service
    with pytest.raises(InvalidSubscriptionStateError):
        initiate_subscription(
            license_id=license.id,
            plan_code="PLUS",
            started_at=now,
            expires_at=now - timedelta(hours=1),
        )

    # Invalid end time via model clean()
    invalid_sub = Subscription(
        license=license,
        plan=license.plan,
        started_at=now,
        expires_at=now,
    )
    with pytest.raises(ValidationError):
        invalid_sub.save()


@pytest.mark.django_db
def test_cannot_initiate_subscription_on_revoked_license(elder):
    license = activate_license(
        elder_id=elder.id,
        plan_code="BASIC",
        valid_from=timezone.now(),
    )
    revoke_license(license_id=license.id)

    with pytest.raises(InvalidLicenseStateError):
        initiate_subscription(
            license_id=license.id,
            plan_code="PLUS",
            duration=timedelta(days=30),
        )


@pytest.mark.django_db
def test_single_active_license_constraint(elder):
    activate_license(
        elder_id=elder.id,
        plan_code="BASIC",
        valid_from=timezone.now(),
    )
    plan_plus = Plan.objects.get(code="PLUS")
    # Attempting to bypass service and directly insert duplicate ACTIVE license hits constraint
    with pytest.raises(IntegrityError):
        License.objects.create(
            elder=elder,
            plan=plan_plus,
            status=LicenseStatus.ACTIVE,
            valid_from=timezone.now(),
        )


@pytest.mark.django_db
def test_get_active_subscription_query(elder):
    now = timezone.now()
    license = activate_license(
        elder_id=elder.id,
        plan_code="BASIC",
        valid_from=now - timedelta(days=5),
    )
    assert get_active_subscription_for_license(license.id) is None

    sub = initiate_subscription(
        license_id=license.id,
        plan_code="PLUS",
        started_at=now - timedelta(days=1),
        expires_at=now + timedelta(days=29),
    )
    activate_subscription(subscription_id=sub.id)

    active = get_active_subscription_for_license(license.id)
    assert active is not None
    assert active.id == sub.id


@pytest.mark.django_db
def test_subscription_renewal_chains_contiguous_period(elder):
    now = timezone.now()
    license = activate_license(
        elder_id=elder.id,
        plan_code="BASIC",
        valid_from=now - timedelta(days=1),
        valid_until=now + timedelta(days=10),
    )
    # Current active subscription expires in 10 days
    sub1 = initiate_subscription(
        license_id=license.id,
        plan_code="PLUS",
        started_at=now - timedelta(days=20),
        expires_at=now + timedelta(days=10),
        auto_renew=True,
    )
    activate_subscription(subscription_id=sub1.id)

    # Renewal created before expiration: starts exactly at sub1.expires_at
    sub2 = renew_subscription(
        subscription_id=sub1.id,
        duration=timedelta(days=30),
    )
    assert sub2.status == SubscriptionStatus.PENDING_PAYMENT
    assert sub2.license_id == license.id
    assert sub2.plan.code == "PLUS"
    assert sub2.started_at == sub1.expires_at
    assert sub2.expires_at == sub1.expires_at + timedelta(days=30)
    assert sub2.auto_renew is True

    # Activate renewal: extends license valid_until to sub2.expires_at
    activate_subscription(subscription_id=sub2.id)
    license.refresh_from_db()
    assert license.valid_until == sub2.expires_at
