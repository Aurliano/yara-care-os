"""Billing pricing catalog services."""

from __future__ import annotations

from decimal import Decimal

from domains.billing.enums import BillingInterval, Currency
from domains.billing.models import PlanPrice


def get_active_price(
    plan_code: str,
    interval: str = BillingInterval.MONTHLY,
    currency: str = Currency.TOMAN,
) -> PlanPrice | None:
    return PlanPrice.objects.filter(
        plan_code=plan_code,
        interval=interval,
        currency=currency,
        is_active=True,
    ).first()


def create_plan_price(
    *,
    plan_code: str,
    amount: Decimal,
    interval: str = BillingInterval.MONTHLY,
    currency: str = Currency.TOMAN,
    is_active: bool = True,
) -> PlanPrice:
    return PlanPrice.objects.create(
        plan_code=plan_code,
        amount=amount,
        interval=interval,
        currency=currency,
        is_active=is_active,
    )
