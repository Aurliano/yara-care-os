"""Workflow API hardening tests."""

import uuid

import pytest
from rest_framework.test import APIClient

from domains.identity_access.services.profiles import create_user


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def authenticated_client(api_client: APIClient, db) -> APIClient:
    user = create_user(phone="+989139999999", password="securepass123", full_name="API Tester")
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
def test_execution_detail_returns_404_for_unknown_execution(authenticated_client: APIClient):
    response = authenticated_client.get(f"/api/v1/executions/{uuid.uuid4()}/")
    assert response.status_code == 404
    assert response.json()["detail"]
