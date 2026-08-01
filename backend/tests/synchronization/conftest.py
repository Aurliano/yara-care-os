import uuid

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from domains.identity_access.services.profiles import create_user


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("migrate", verbosity=0)
        call_command("seed_identity_access", verbosity=0)


@pytest.fixture
def sync_user(db):
    return create_user(
        phone="+989135555555",
        password="securepass123",
        full_name="Sync Tester",
    )


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def authenticated_client(api_client: APIClient, sync_user) -> APIClient:
    api_client.force_authenticate(user=sync_user)
    return api_client


@pytest.fixture
def hub_replica_id() -> uuid.UUID:
    return uuid.uuid4()
