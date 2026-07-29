import uuid
from datetime import timedelta

import pytest
from django.utils import timezone

from domains.event.services.recording import EventInput, record_event


@pytest.mark.django_db
def test_query_api_is_read_only(authenticated_client):
    event_id = uuid.uuid4()
    occurred_at = timezone.now() - timedelta(hours=4)
    record_event(
        EventInput(
            event_id=event_id,
            event_type="LicensePlanChanged",
            event_version=1,
            producer="licensing",
            occurred_at=occurred_at,
            correlation_id="corr-api-1",
            causation_id="cause-api-1",
            payload={"from_plan": "BASIC", "to_plan": "PLUS"},
        )
    )

    detail_response = authenticated_client.get(f"/api/v1/events/{event_id}/")
    assert detail_response.status_code == 200
    assert detail_response.json()["producer"] == "licensing"
    assert "elder_id" not in detail_response.json()

    correlation_response = authenticated_client.get(
        "/api/v1/events/",
        {"correlation_id": "corr-api-1"},
    )
    assert correlation_response.status_code == 200
    assert len(correlation_response.json()) == 1


@pytest.mark.django_db
def test_record_and_publish_endpoints_are_not_exposed(authenticated_client):
    event_id = uuid.uuid4()
    body = {
        "event_id": str(event_id),
        "event_type": "LicenseActivated",
        "event_version": 1,
        "producer": "licensing",
        "occurred_at": timezone.now().isoformat(),
        "payload": {"plan_code": "BASIC"},
    }

    create_response = authenticated_client.post("/api/v1/events/", body, format="json")
    assert create_response.status_code == 405

    publish_response = authenticated_client.post(f"/api/v1/events/{event_id}/publish/")
    assert publish_response.status_code == 404
