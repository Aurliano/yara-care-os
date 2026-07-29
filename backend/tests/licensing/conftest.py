import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from domains.identity_access.services.profiles import create_elder, create_user


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("migrate", verbosity=0)
        call_command("seed_identity_access", verbosity=0)
        call_command("seed_licensing", verbosity=0)


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user(db):
    return create_user(
        phone="+989131111111",
        password="securepass123",
        full_name="License Owner",
    )


@pytest.fixture
def elder(db, user):
    return create_elder(actor=user, full_name="Licensed Elder")


@pytest.fixture
def authenticated_client(api_client: APIClient, user) -> APIClient:
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def second_user(db):
    return create_user(
        phone="+989131111112",
        password="securepass123",
        full_name="Caregiver User",
    )
