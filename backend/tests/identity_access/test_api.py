import pytest
from django.utils import timezone
from datetime import timedelta

from domains.identity_access.services.invitations import create_invitation


@pytest.mark.django_db
def test_register_and_login_flow(api_client):
    register_response = api_client.post(
        "/api/v1/auth/register/",
        {
            "phone": "+989123456789",
            "password": "securepass123",
            "full_name": "New User",
            "email": "new@example.com",
        },
        format="json",
    )
    assert register_response.status_code == 201

    token_response = api_client.post(
        "/api/v1/auth/token/",
        {"phone": "+989123456789", "password": "securepass123"},
        format="json",
    )
    assert token_response.status_code == 200
    assert "access" in token_response.json()
    assert "refresh" in token_response.json()


@pytest.mark.django_db
def test_create_elder_and_list(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/elders/",
        {"full_name": "Father", "birth_date": "1940-01-01"},
        format="json",
    )
    assert response.status_code == 201
    elder_id = response.json()["id"]

    list_response = authenticated_client.get("/api/v1/elders/")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["id"] == elder_id


@pytest.mark.django_db
def test_health_endpoint_still_works(api_client):
    response = api_client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_permission_check_api(authenticated_client, elder):
    response = authenticated_client.post(
        f"/api/v1/elders/{elder.id}/permissions/check/",
        {"permission_code": "MANAGE_MEMBERS"},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["allowed"] is True


@pytest.mark.django_db
def test_invitation_api_flow(authenticated_client, elder, second_user, api_client):
    create_response = authenticated_client.post(
        f"/api/v1/elders/{elder.id}/invitations/",
        {"expires_at": (timezone.now() + timedelta(days=3)).isoformat()},
        format="json",
    )
    assert create_response.status_code == 201
    invite_code = create_response.json()["invite_code"]

    api_client.force_authenticate(user=second_user)
    accept_response = api_client.post(
        "/api/v1/invitations/accept/",
        {"invite_code": invite_code},
        format="json",
    )
    assert accept_response.status_code == 201
    assert accept_response.json()["role_code"] == "VIEWER"
