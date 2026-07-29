from django.core.management import call_command


def test_django_boots() -> None:
    call_command("check")


def test_health_endpoint(api_client) -> None:
    response = api_client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
