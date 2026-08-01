import uuid

import pytest
from django.core.management import call_command

from domains.identity_access.models import EmergencyRecipient
from domains.identity_access.services.profiles import create_elder, create_user
from domains.licensing.services.licenses import activate_license
from rest_framework.test import APIClient


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("migrate", verbosity=0)
        call_command("seed_identity_access", verbosity=0)
        call_command("seed_licensing", verbosity=0)


@pytest.fixture
def comm_user(db):
    return create_user(
        phone="+989134444444",
        password="securepass123",
        full_name="Communication Tester",
    )


@pytest.fixture
def elder(db, comm_user):
    return create_elder(actor=comm_user, full_name="Communication Elder")


@pytest.fixture
def licensed_elder(elder):
    activate_license(elder_id=elder.id, plan_code="BASIC")
    return elder


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def authenticated_client(api_client: APIClient, comm_user) -> APIClient:
    api_client.force_authenticate(user=comm_user)
    return api_client
