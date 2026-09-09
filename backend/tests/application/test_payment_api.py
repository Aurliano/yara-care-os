"""Tests for Payment REST API endpoints."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from domains.billing.enums import BillingInterval, Currency
from domains.billing.services.pricing import create_plan_price
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
from domains.licensing.enums import LicenseStatus, PlanStatus
from domains.licensing.models import License, Plan
from infrastructure.payment.factory import reset_fake_provider

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def clean_fake_provider():
    reset_fake_provider()
    yield
    reset_fake_provider()


@pytest.fixture
def api_test_data(db):
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

    primary_user = User.objects.create(
        phone="+989121111111",
        full_name="Primary Caregiver",
        status=UserStatus.ACTIVE,
    )
    secondary_user = User.objects.create(
        phone="+989122222222",
        full_name="Secondary Caregiver",
        status=UserStatus.ACTIVE,
    )

    elder = Elder.objects.create(full_name="Grandpa Joe")

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

    plan = Plan.objects.create(
        code="PREMIUM",
        name="Premium Care",
        status=PlanStatus.ACTIVE,
    )

    create_plan_price(
        plan_code="PREMIUM",
        amount=Decimal("300000"),
        interval=BillingInterval.MONTHLY,
        currency=Currency.TOMAN,
    )

    License.objects.create(
        elder=elder,
        plan=plan,
        status=LicenseStatus.ACTIVE,
        valid_from=timezone.now(),
        valid_until=timezone.now() + timedelta(days=30),
    )

    return {
        "primary_user": primary_user,
        "secondary_user": secondary_user,
        "elder": elder,
    }


def test_checkout_endpoint_requires_authentication():
    client = APIClient()
    response = client.post("/api/v1/payments/checkout/", {}, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_checkout_endpoint_permission_denied_for_secondary_caregiver(api_test_data):
    client = APIClient()
    client.force_authenticate(user=api_test_data["secondary_user"])

    payload = {
        "elder_id": str(api_test_data["elder"].id),
        "plan_code": "PREMIUM",
        "interval": "MONTHLY",
    }
    response = client.post("/api/v1/payments/checkout/", payload, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_checkout_endpoint_success_for_primary_caregiver(api_test_data):
    client = APIClient()
    client.force_authenticate(user=api_test_data["primary_user"])

    payload = {
        "elder_id": str(api_test_data["elder"].id),
        "plan_code": "PREMIUM",
        "interval": "MONTHLY",
    }
    response = client.post("/api/v1/payments/checkout/", payload, format="json")
    assert response.status_code == status.HTTP_200_OK

    data = response.data
    assert "provider_reference" in data
    assert "redirect_url" in data
    assert data["amount"] == "300000"
    assert data["currency"] == "TOMAN"


def test_checkout_endpoint_ignores_client_tampered_amount(api_test_data):
    client = APIClient()
    client.force_authenticate(user=api_test_data["primary_user"])

    # Malicious payload trying to set amount to 1 Toman
    payload = {
        "elder_id": str(api_test_data["elder"].id),
        "plan_code": "PREMIUM",
        "interval": "MONTHLY",
        "amount": "1",
        "currency": "USD",
    }
    response = client.post("/api/v1/payments/checkout/", payload, format="json")
    assert response.status_code == status.HTTP_200_OK

    # Server strictly resolves authoritative price from PlanPrice (300000 TOMAN)
    assert response.data["amount"] == "300000"
    assert response.data["currency"] == "TOMAN"


def test_verify_endpoint_success(api_test_data):
    client = APIClient()
    client.force_authenticate(user=api_test_data["primary_user"])

    # First initiate checkout
    checkout_resp = client.post(
        "/api/v1/payments/checkout/",
        {
            "elder_id": str(api_test_data["elder"].id),
            "plan_code": "PREMIUM",
        },
        format="json",
    )
    authority = checkout_resp.data["provider_reference"]

    # Bank returns to verify endpoint (AllowAny)
    unauth_client = APIClient()
    verify_resp = unauth_client.get(
        f"/api/v1/payments/verify/?Authority={authority}&Status=OK"
    )
    assert verify_resp.status_code == status.HTTP_200_OK
    assert verify_resp.data["is_successful"] is True
    assert verify_resp.data["provider_reference"] == authority
    assert verify_resp.data["already_settled"] is False


def test_verify_endpoint_gateway_cancelled(api_test_data):
    client = APIClient()
    client.force_authenticate(user=api_test_data["primary_user"])

    checkout_resp = client.post(
        "/api/v1/payments/checkout/",
        {
            "elder_id": str(api_test_data["elder"].id),
            "plan_code": "PREMIUM",
        },
        format="json",
    )
    authority = checkout_resp.data["provider_reference"]

    unauth_client = APIClient()
    verify_resp = unauth_client.get(
        f"/api/v1/payments/verify/?Authority={authority}&Status=NOK"
    )
    assert verify_resp.status_code == status.HTTP_200_OK
    assert verify_resp.data["is_successful"] is False
    assert verify_resp.data["error_code"] == "CANCELLED_BY_USER"


def test_verify_endpoint_unknown_authority():
    client = APIClient()
    response = client.get("/api/v1/payments/verify/?Authority=UNKNOWN-REF")
    assert response.status_code == status.HTTP_404_NOT_FOUND
