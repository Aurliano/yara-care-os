"""License lifecycle operations."""

from __future__ import annotations

import uuid
from datetime import datetime

from django.db import transaction
from django.utils import timezone

from domains.licensing.enums import LicenseStatus, PlanStatus
from domains.licensing.exceptions import InvalidLicenseStateError, LicenseNotFoundError
from domains.licensing.models import License, LicensePlanHistory, Plan


def persist_license_expiration_if_due(license: License) -> bool:
    """Persist EXPIRED outside caller transactions when validity has ended."""
    if license.valid_until is None:
        return False

    updated = License.objects.filter(
        pk=license.pk,
        status=LicenseStatus.ACTIVE,
        valid_until__lt=timezone.now(),
    ).update(status=LicenseStatus.EXPIRED)
    if updated:
        license.refresh_from_db()
        return True
    return False


def get_active_license_for_elder(elder_id: uuid.UUID) -> License | None:
    license = (
        License.objects.filter(elder_id=elder_id, status=LicenseStatus.ACTIVE)
        .select_related("plan")
        .order_by("-created_at")
        .first()
    )
    if license is None:
        return None

    if persist_license_expiration_if_due(license):
        return None

    if license.valid_from > timezone.now():
        return None
    if license.valid_until is not None and license.valid_until < timezone.now():
        return None
    return license


def get_license(license_id: uuid.UUID) -> License:
    return License.objects.select_related("plan", "elder").get(pk=license_id)


@transaction.atomic
def activate_license(
    *,
    elder_id: uuid.UUID,
    plan_code: str,
    valid_from: datetime | None = None,
    valid_until: datetime | None = None,
) -> License:
    plan = Plan.objects.get(code=plan_code, status=PlanStatus.ACTIVE)
    starts_at = valid_from or timezone.now()

    existing_active = License.objects.filter(
        elder_id=elder_id,
        status=LicenseStatus.ACTIVE,
    ).exists()
    if existing_active:
        raise InvalidLicenseStateError("Elder already has an active license.")

    return License.objects.create(
        elder_id=elder_id,
        plan=plan,
        status=LicenseStatus.ACTIVE,
        valid_from=starts_at,
        valid_until=valid_until,
    )


@transaction.atomic
def change_license_plan(*, license_id: uuid.UUID, plan_code: str) -> License:
    license = License.objects.select_for_update().select_related("plan").get(pk=license_id)
    if license.status not in {LicenseStatus.ACTIVE, LicenseStatus.SUSPENDED}:
        raise InvalidLicenseStateError("Only active or suspended licenses can change plan.")

    new_plan = Plan.objects.get(code=plan_code, status=PlanStatus.ACTIVE)
    if new_plan.pk == license.plan_id:
        return license

    LicensePlanHistory.objects.create(
        license=license,
        previous_plan=license.plan,
        new_plan=new_plan,
    )
    license.plan = new_plan
    license.save(update_fields=["plan"])
    return license


@transaction.atomic
def suspend_license(*, license_id: uuid.UUID) -> License:
    license = License.objects.select_for_update().get(pk=license_id)
    if license.status != LicenseStatus.ACTIVE:
        raise InvalidLicenseStateError("Only active licenses can be suspended.")
    license.status = LicenseStatus.SUSPENDED
    license.save(update_fields=["status"])
    return license


@transaction.atomic
def resume_license(*, license_id: uuid.UUID) -> License:
    license = License.objects.select_for_update().get(pk=license_id)
    if license.status != LicenseStatus.SUSPENDED:
        raise InvalidLicenseStateError("Only suspended licenses can be resumed.")
    if license.valid_until is not None and license.valid_until < timezone.now():
        raise InvalidLicenseStateError("Cannot resume an expired license.")
    license.status = LicenseStatus.ACTIVE
    license.save(update_fields=["status"])
    return license


def expire_license(*, license_id: uuid.UUID) -> License:
    with transaction.atomic():
        license = License.objects.select_for_update().get(pk=license_id)
        if license.status == LicenseStatus.REVOKED:
            raise InvalidLicenseStateError("Revoked licenses cannot be expired.")
        if license.status == LicenseStatus.EXPIRED:
            return license
        license.status = LicenseStatus.EXPIRED
        license.save(update_fields=["status"])
    return license


def revoke_license(*, license_id: uuid.UUID) -> License:
    with transaction.atomic():
        license = License.objects.select_for_update().get(pk=license_id)
        if license.status == LicenseStatus.REVOKED:
            return license
        license.status = LicenseStatus.REVOKED
        license.save(update_fields=["status"])
    return license
