"""Plan and entitlement configuration."""

from __future__ import annotations

from django.db import transaction

from domains.licensing.enums import EntitlementKind, PlanStatus
from domains.licensing.exceptions import InvalidEntitlementError
from domains.licensing.models import Entitlement, Plan, PlanEntitlement


@transaction.atomic
def create_plan(*, code: str, name: str) -> Plan:
    return Plan.objects.create(code=code, name=name, status=PlanStatus.ACTIVE)


@transaction.atomic
def update_plan(*, plan: Plan, name: str | None = None, status: str | None = None) -> Plan:
    update_fields = []
    if name is not None:
        plan.name = name
        update_fields.append("name")
    if status is not None:
        plan.status = status
        update_fields.append("status")
    if update_fields:
        plan.save(update_fields=update_fields)
    return plan


@transaction.atomic
def configure_plan_entitlement(
    *,
    plan: Plan,
    entitlement_key: str,
    kind: str,
    value: str,
    description: str = "",
) -> PlanEntitlement:
    entitlement, _ = Entitlement.objects.get_or_create(
        key=entitlement_key,
        defaults={"kind": kind, "description": description},
    )
    if entitlement.kind != kind:
        raise InvalidEntitlementError("Entitlement kind does not match existing definition.")

    plan_entitlement, _ = PlanEntitlement.objects.update_or_create(
        plan=plan,
        entitlement=entitlement,
        defaults={"value": value},
    )
    return plan_entitlement


def get_plan(plan_code: str) -> Plan:
    return Plan.objects.prefetch_related("plan_entitlements__entitlement").get(code=plan_code)
