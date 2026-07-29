import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from domains.identity_access.enums import RoleCode
from domains.identity_access.models import User
from domains.identity_access.services.profiles import create_elder, create_user


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("migrate", verbosity=0)
        call_command("seed_identity_access", verbosity=0)


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user(db) -> User:
    return create_user(
        phone="+989121234567",
        password="securepass123",
        full_name="Ali Caregiver",
        email="ali@example.com",
    )


@pytest.fixture
def authenticated_client(api_client: APIClient, user: User) -> APIClient:
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def elder(db, user: User):
    return create_elder(actor=user, full_name="Mother")


@pytest.fixture
def second_user(db) -> User:
    return create_user(
        phone="+989121234568",
        password="securepass123",
        full_name="Sara Caregiver",
    )


@pytest.fixture
def viewer_user(db) -> User:
    return create_user(
        phone="+989121234569",
        password="securepass123",
        full_name="Viewer User",
    )
