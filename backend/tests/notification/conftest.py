import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

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
def notification_user(db):
    return create_user(
        phone="+989134444444",
        password="securepass123",
        full_name="Notification Tester",
    )


@pytest.fixture
def elder(db, notification_user):
    return create_elder(actor=notification_user, full_name="Notification Elder")


@pytest.fixture
def licensed_elder(elder):
    return elder


@pytest.fixture
def recurrence_definition():
    return {"type": "daily", "time": "08:00"}


@pytest.fixture
def schedule_start_at():
    from datetime import datetime
    from zoneinfo import ZoneInfo

    return datetime(2026, 8, 1, 0, 0, tzinfo=ZoneInfo("UTC"))


@pytest.fixture
def authenticated_client(api_client: APIClient, notification_user) -> APIClient:
    api_client.force_authenticate(user=notification_user)
    return api_client
