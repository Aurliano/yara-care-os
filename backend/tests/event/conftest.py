import pytest
from rest_framework.test import APIClient

from domains.identity_access.services.profiles import create_user


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def authenticated_client(api_client: APIClient, db) -> APIClient:
    user = create_user(
        phone="+989141111111",
        password="securepass123",
        full_name="Event Tester",
    )
    api_client.force_authenticate(user=user)
    return api_client
