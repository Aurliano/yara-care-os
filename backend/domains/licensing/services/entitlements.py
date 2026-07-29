"""Entitlement evaluation queries."""

from __future__ import annotations

import uuid
from typing import Any

from domains.licensing.enums import EntitlementKind
from domains.licensing.exceptions import InvalidEntitlementError, LicenseNotFoundError
from domains.licensing.models import Entitlement, License, PlanEntitlement
from domains.licensing.services.licenses import get_active_license_for_elder


def _get_plan_entitlement(license: License, entitlement_key: str) -> PlanEntitlement | None:
    return (
        PlanEntitlement.objects.select_related("entitlement")
        .filter(plan=license.plan, entitlement__key=entitlement_key)
        .first()
    )


def _require_active_license(elder_id: uuid.UUID) -> License:
    license = get_active_license_for_elder(elder_id)
    if license is None:
        raise LicenseNotFoundError("No active license found for this Elder.")
    return license


def get_entitlement(elder_id: uuid.UUID, entitlement_key: str) -> str | None:
    """Return the raw entitlement value for an Elder, or None if unavailable."""
    try:
        license = _require_active_license(elder_id)
    except LicenseNotFoundError:
        return None

    plan_entitlement = _get_plan_entitlement(license, entitlement_key)
    if plan_entitlement is None:
        return None
    return plan_entitlement.value


def has_entitlement(elder_id: uuid.UUID, entitlement_key: str) -> bool:
    """Return whether a feature entitlement is enabled for an Elder."""
    value = get_entitlement(elder_id, entitlement_key)
    if value is None:
        return False

    entitlement = Entitlement.objects.filter(key=entitlement_key).first()
    if entitlement is None:
        return False
    if entitlement.kind != EntitlementKind.FEATURE:
        raise InvalidEntitlementError(f"{entitlement_key} is not a feature entitlement.")
    return value.lower() in {"true", "enabled", "1"}


def get_limit(elder_id: uuid.UUID, entitlement_key: str) -> int | None:
    """Return a limit entitlement value for an Elder."""
    value = get_entitlement(elder_id, entitlement_key)
    if value is None:
        return None

    entitlement = Entitlement.objects.filter(key=entitlement_key).first()
    if entitlement is None:
        return None
    if entitlement.kind != EntitlementKind.LIMIT:
        raise InvalidEntitlementError(f"{entitlement_key} is not a limit entitlement.")
    return int(value)


def can_use_feature(elder_id: uuid.UUID, entitlement_key: str) -> bool:
    """Stable consumer interface for feature entitlement checks."""
    return has_entitlement(elder_id, entitlement_key)


def evaluate_entitlements_for_elder(elder_id: uuid.UUID) -> dict[str, Any]:
    """Return entitlement map for an active Elder license."""
    license = get_active_license_for_elder(elder_id)
    if license is None:
        return {}

    entitlements: dict[str, Any] = {}
    for plan_entitlement in PlanEntitlement.objects.filter(plan=license.plan).select_related(
        "entitlement"
    ):
        key = plan_entitlement.entitlement.key
        if plan_entitlement.entitlement.kind == EntitlementKind.LIMIT:
            entitlements[key] = int(plan_entitlement.value)
        else:
            entitlements[key] = plan_entitlement.value.lower() in {"true", "enabled", "1"}
    return entitlements
