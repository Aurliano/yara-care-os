"""Licensing domain models."""

from __future__ import annotations

import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from domains.licensing.enums import EntitlementKind, LicenseStatus, PlanStatus, SubscriptionStatus


class Plan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    status = models.CharField(
        max_length=16,
        choices=PlanStatus.choices,
        default=PlanStatus.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "licensing_plan"

    def __str__(self) -> str:
        return self.code


class Entitlement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=64, unique=True)
    kind = models.CharField(max_length=16, choices=EntitlementKind.choices)
    description = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "licensing_entitlement"

    def __str__(self) -> str:
        return self.key


class PlanEntitlement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(
        Plan,
        on_delete=models.CASCADE,
        related_name="plan_entitlements",
    )
    entitlement = models.ForeignKey(
        Entitlement,
        on_delete=models.CASCADE,
        related_name="plan_entitlements",
    )
    value = models.CharField(max_length=64)

    class Meta:
        db_table = "licensing_plan_entitlement"
        constraints = [
            models.UniqueConstraint(
                fields=["plan", "entitlement"],
                name="licensing_plan_entitlement_unique",
            ),
        ]

    def clean(self) -> None:
        if self.entitlement.kind == EntitlementKind.LIMIT:
            try:
                limit_value = int(self.value)
            except ValueError as exc:
                raise ValidationError({"value": "Limit entitlements require an integer value."}) from exc
            if limit_value < 0:
                raise ValidationError({"value": "Limit entitlements cannot be negative."})
        if self.entitlement.kind == EntitlementKind.FEATURE and self.value.lower() not in {
            "true",
            "false",
            "enabled",
            "disabled",
            "1",
            "0",
        }:
            raise ValidationError({"value": "Feature entitlements require a boolean-like value."})

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)


class License(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    elder = models.ForeignKey(
        "identity_access.Elder",
        on_delete=models.PROTECT,
        related_name="licenses",
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="licenses",
    )
    status = models.CharField(
        max_length=16,
        choices=LicenseStatus.choices,
        default=LicenseStatus.ACTIVE,
    )
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "licensing_license"
        constraints = [
            models.CheckConstraint(
                condition=Q(valid_until__isnull=True) | Q(valid_until__gte=models.F("valid_from")),
                name="licensing_license_valid_window",
            ),
            models.UniqueConstraint(
                fields=["elder"],
                condition=Q(status=LicenseStatus.ACTIVE),
                name="licensing_license_single_active_per_elder",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.elder_id}:{self.plan.code}:{self.status}"


class LicensePlanHistory(models.Model):
    """Audit record of plan changes for a License aggregate.

    Minimal history only — not subscription or billing history.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    license = models.ForeignKey(
        License,
        on_delete=models.CASCADE,
        related_name="plan_history",
    )
    previous_plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="previous_license_plans",
    )
    new_plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="new_license_plans",
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "licensing_license_plan_history"


class Subscription(models.Model):
    """Temporal commercial commitment supporting a License.

    Defines an active term for which commercial access is valid.
    Supports arbitrary durations (trials, monthly, annual, short-term rentals).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    license = models.ForeignKey(
        License,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )
    status = models.CharField(
        max_length=16,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.PENDING_PAYMENT,
    )
    started_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    auto_renew = models.BooleanField(default=False)
    is_trial = models.BooleanField(default=False)
    payer_user_id = models.UUIDField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "licensing_subscription"
        constraints = [
            models.CheckConstraint(
                condition=Q(expires_at__gt=models.F("started_at")),
                name="licensing_subscription_valid_window",
            ),
        ]

    def clean(self) -> None:
        if self.started_at and self.expires_at and self.expires_at <= self.started_at:
            raise ValidationError({"expires_at": "Subscription expiration must be strictly after start time."})

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.license_id}:{self.plan.code}:{self.status}:{self.expires_at}"
