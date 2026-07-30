from datetime import datetime, timedelta

import pytest
from django.utils import timezone
from zoneinfo import ZoneInfo

from domains.scheduling.models import Occurrence
from domains.scheduling.services.schedules import create_schedule
from tests.scheduling.conftest import _aware


@pytest.mark.django_db
def test_create_and_query_schedule_api(authenticated_client):
    start_at = _aware(datetime(2026, 7, 1, 0, 0, tzinfo=ZoneInfo("UTC")))
    response = authenticated_client.post(
        "/api/v1/schedules/",
        {
            "owner_reference": "care_activity:api-1",
            "recurrence_definition": {"type": "daily", "time": "08:00"},
            "timezone": "Asia/Tehran",
            "start_at": start_at.isoformat(),
        },
        format="json",
    )
    assert response.status_code == 201
    schedule_id = response.json()["id"]

    detail = authenticated_client.get(f"/api/v1/schedules/{schedule_id}/")
    assert detail.status_code == 200

    occurrences = authenticated_client.get(f"/api/v1/schedules/{schedule_id}/occurrences/")
    assert occurrences.status_code == 200
    assert len(occurrences.json()) > 0


@pytest.mark.django_db
def test_due_processing_not_exposed_as_rest_endpoint(authenticated_client):
    import uuid

    response = authenticated_client.post(f"/api/v1/occurrences/{uuid.uuid4()}/due/")
    assert response.status_code == 404
