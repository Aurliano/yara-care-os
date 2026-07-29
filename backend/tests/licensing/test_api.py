import pytest
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_license_activate_and_entitlement_api(authenticated_client, elder):
    activate_response = authenticated_client.post(
        f"/api/v1/elders/{elder.id}/license/activate/",
        {
            "plan_code": "PLUS",
            "valid_from": (timezone.now() - timedelta(days=1)).isoformat(),
            "valid_until": (timezone.now() + timedelta(days=30)).isoformat(),
        },
        format="json",
    )
    assert activate_response.status_code == 201
    license_id = activate_response.json()["id"]

    license_response = authenticated_client.get(f"/api/v1/elders/{elder.id}/license/")
    assert license_response.status_code == 200
    assert license_response.json()["plan_code"] == "PLUS"

    check_response = authenticated_client.post(
        f"/api/v1/elders/{elder.id}/entitlements/check/",
        {"entitlement_key": "SENSOR_SUPPORT"},
        format="json",
    )
    assert check_response.status_code == 200
    assert check_response.json()["allowed"] is True

    limit_response = authenticated_client.get(
        f"/api/v1/elders/{elder.id}/entitlements/limits/MAX_CAREGIVERS/"
    )
    assert limit_response.status_code == 200
    assert limit_response.json()["limit"] == 5

    suspend_response = authenticated_client.post(
        f"/api/v1/elders/{elder.id}/license/{license_id}/suspend/",
        format="json",
    )
    assert suspend_response.status_code == 200
    assert suspend_response.json()["status"] == "SUSPENDED"


@pytest.mark.django_db
def test_plan_list_api(authenticated_client):
    response = authenticated_client.get("/api/v1/plans/")
    assert response.status_code == 200
    codes = {plan["code"] for plan in response.json()}
    assert {"BASIC", "PLUS", "PREMIUM"}.issubset(codes)


@pytest.mark.django_db
def test_license_admin_requires_manage_subscription(authenticated_client, elder, second_user):
    from domains.identity_access.enums import MembershipStatus, RoleCode
    from domains.identity_access.services.memberships import create_membership

    create_membership(
        user=second_user,
        elder=elder,
        role_code=RoleCode.CAREGIVER,
        status=MembershipStatus.ACTIVE,
    )
    caregiver_client = APIClient()
    caregiver_client.force_authenticate(user=second_user)
    response = caregiver_client.post(
        f"/api/v1/elders/{elder.id}/license/activate/",
        {
            "plan_code": "BASIC",
            "valid_from": (timezone.now() - timedelta(days=1)).isoformat(),
        },
        format="json",
    )
    assert response.status_code == 403

    activate_response = authenticated_client.post(
        f"/api/v1/elders/{elder.id}/license/activate/",
        {
            "plan_code": "BASIC",
            "valid_from": (timezone.now() - timedelta(days=1)).isoformat(),
        },
        format="json",
    )
    assert activate_response.status_code == 201
