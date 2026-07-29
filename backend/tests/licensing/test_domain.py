import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

from domains.licensing.enums import EntitlementKey, EntitlementKind, LicenseStatus
from domains.licensing.exceptions import InvalidEntitlementError, InvalidLicenseStateError
from domains.licensing.models import Entitlement, License, LicensePlanHistory, Plan, PlanEntitlement
from domains.licensing.services.entitlements import (
    can_use_feature,
    get_entitlement,
    get_limit,
    has_entitlement,
)
from domains.licensing.services.licenses import (
    activate_license,
    change_license_plan,
    expire_license,
    get_active_license_for_elder,
    persist_license_expiration_if_due,
    resume_license,
    revoke_license,
    suspend_license,
)
from domains.identity_access.services.profiles import create_elder
from domains.licensing.services.plans import create_plan


@pytest.mark.django_db
def test_plan_entitlement_configuration(elder):
    plan = Plan.objects.get(code="BASIC")
    entitlement = Entitlement.objects.get(key=EntitlementKey.MAX_CAREGIVERS)
    plan_entitlement = PlanEntitlement.objects.get(plan=plan, entitlement=entitlement)
    assert plan_entitlement.value == "2"


@pytest.mark.django_db
def test_entitlement_keys_are_unique():
    keys = list(Entitlement.objects.values_list("key", flat=True))
    assert len(keys) == len(set(keys))


@pytest.mark.django_db
def test_negative_limit_rejected(elder):
    plan = create_plan(code="TEST_PLAN", name="Test")
    entitlement = Entitlement.objects.create(
        key="TEST_LIMIT",
        kind=EntitlementKind.LIMIT,
        description="test",
    )
    with pytest.raises(ValidationError):
        PlanEntitlement.objects.create(plan=plan, entitlement=entitlement, value="-1")


@pytest.mark.django_db
def test_active_license_grants_entitlements(elder):
    license = activate_license(
        elder_id=elder.id,
        plan_code="PREMIUM",
        valid_from=timezone.now() - timedelta(days=1),
        valid_until=timezone.now() + timedelta(days=30),
    )
    assert license.status == LicenseStatus.ACTIVE
    assert can_use_feature(elder.id, EntitlementKey.VIDEO_CALL) is True
    assert get_limit(elder.id, EntitlementKey.MAX_CAREGIVERS) == 10


@pytest.mark.django_db
def test_suspended_license_denies_entitlements(elder):
    license = activate_license(
        elder_id=elder.id,
        plan_code="PREMIUM",
        valid_from=timezone.now() - timedelta(days=1),
    )
    suspend_license(license_id=license.id)
    assert get_entitlement(elder.id, EntitlementKey.VIDEO_CALL) is None
    assert can_use_feature(elder.id, EntitlementKey.VIDEO_CALL) is False


@pytest.mark.django_db
def test_revoked_license_denies_entitlements(elder):
    license = activate_license(
        elder_id=elder.id,
        plan_code="PLUS",
        valid_from=timezone.now() - timedelta(days=1),
    )
    revoke_license(license_id=license.id)
    assert get_limit(elder.id, EntitlementKey.MAX_CAREGIVERS) is None


@pytest.mark.django_db
def test_expired_license_persisted_and_denies_entitlements(elder):
    license = activate_license(
        elder_id=elder.id,
        plan_code="PLUS",
        valid_from=timezone.now() - timedelta(days=10),
        valid_until=timezone.now() - timedelta(hours=1),
    )
    assert persist_license_expiration_if_due(license) is True
    license.refresh_from_db()
    assert license.status == LicenseStatus.EXPIRED
    assert get_active_license_for_elder(elder.id) is None


@pytest.mark.django_db
def test_valid_from_blocks_future_license(elder):
    activate_license(
        elder_id=elder.id,
        plan_code="BASIC",
        valid_from=timezone.now() + timedelta(days=1),
    )
    assert get_active_license_for_elder(elder.id) is None


@pytest.mark.django_db
def test_plan_change_preserves_license_history(elder):
    license = activate_license(
        elder_id=elder.id,
        plan_code="BASIC",
        valid_from=timezone.now() - timedelta(days=1),
    )
    original_id = license.id
    change_license_plan(license_id=license.id, plan_code="PREMIUM")
    license.refresh_from_db()
    assert license.id == original_id
    assert license.plan.code == "PREMIUM"
    history = LicensePlanHistory.objects.get(license=license)
    assert history.previous_plan.code == "BASIC"
    assert history.new_plan.code == "PREMIUM"
    assert get_limit(elder.id, EntitlementKey.MAX_CAREGIVERS) == 10


@pytest.mark.django_db
def test_consumers_use_entitlement_keys_not_plan_names(elder):
    activate_license(
        elder_id=elder.id,
        plan_code="PREMIUM",
        valid_from=timezone.now() - timedelta(days=1),
    )
    assert can_use_feature(elder.id, "VIDEO_CALL") is True
    assert get_limit(elder.id, "MAX_HUBS") == 1


@pytest.mark.django_db
def test_limit_entitlement_type_guard(elder):
    activate_license(
        elder_id=elder.id,
        plan_code="BASIC",
        valid_from=timezone.now() - timedelta(days=1),
    )
    with pytest.raises(InvalidEntitlementError):
        has_entitlement(elder.id, EntitlementKey.MAX_CAREGIVERS)


@pytest.mark.django_db
def test_cross_elder_entitlement_isolation(elder, user):
    other_elder = create_elder(actor=user, full_name="Other Licensed Elder")
    activate_license(
        elder_id=elder.id,
        plan_code="PREMIUM",
        valid_from=timezone.now() - timedelta(days=1),
    )
    activate_license(
        elder_id=other_elder.id,
        plan_code="BASIC",
        valid_from=timezone.now() - timedelta(days=1),
    )
    assert can_use_feature(elder.id, EntitlementKey.VIDEO_CALL) is True
    assert can_use_feature(other_elder.id, EntitlementKey.VIDEO_CALL) is False


@pytest.mark.django_db
def test_activate_duplicate_active_license_rejected(elder):
    activate_license(
        elder_id=elder.id,
        plan_code="BASIC",
        valid_from=timezone.now() - timedelta(days=1),
    )
    with pytest.raises(InvalidLicenseStateError):
        activate_license(
            elder_id=elder.id,
            plan_code="PLUS",
            valid_from=timezone.now(),
        )
