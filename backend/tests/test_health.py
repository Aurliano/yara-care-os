"""Health endpoint tests."""

import pytest


@pytest.mark.django_db
def test_health_endpoint_returns_readiness_checks(api_client) -> None:
    response = api_client.get("/api/v1/health/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"ok", "degraded"}
    assert "checks" in payload
    assert payload["checks"]["database"]["status"] == "ok"
    assert "event_outbox" in payload["checks"]
    assert "integration_dispatcher" in payload["checks"]
    assert "synchronization" in payload["checks"]
