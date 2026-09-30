"""Health endpoint tests."""

import logging
from unittest.mock import patch

from django.db import DatabaseError
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


@pytest.mark.django_db
def test_health_endpoint_sanitizes_database_exception_and_logs(api_client, caplog) -> None:
    sensitive_raw_error = (
        "FATAL: password authentication failed for user 'postgres_superuser' "
        "at server 10.150.0.12:5432; SELECT * FROM sensitive_table"
    )

    integration_logger = logging.getLogger("yara.integration")
    integration_logger.addHandler(caplog.handler)
    try:
        with caplog.at_level(logging.ERROR, logger="yara.integration"):
            with patch("django.db.connection.ensure_connection", side_effect=DatabaseError(sensitive_raw_error)):
                response = api_client.get("/api/v1/health/")
    finally:
        integration_logger.removeHandler(caplog.handler)

    # 1. HTTP 503 Service Unavailable
    assert response.status_code == 503

    payload = response.json()
    assert payload["status"] == "error"
    assert payload["checks"]["database"]["status"] == "error"

    # 2. Stable generic public detail without internal disclosure
    assert payload["checks"]["database"]["detail"] == "Database connectivity check failed."

    # 3. No sensitive internal details appear anywhere in the serialized response
    raw_response_text = response.content.decode("utf-8")
    assert "postgres_superuser" not in raw_response_text
    assert "10.150.0.12" not in raw_response_text
    assert "sensitive_table" not in raw_response_text
    assert "FATAL" not in raw_response_text
    assert "password" not in raw_response_text
    assert "SELECT" not in raw_response_text

    # 4. Real exception is observable through server-side logging
    assert any("Database connectivity health probe failed" in record.message for record in caplog.records)
    assert any(sensitive_raw_error in record.message or (record.exc_info and sensitive_raw_error in str(record.exc_info)) for record in caplog.records)


@pytest.mark.django_db
def test_liveness_endpoint_returns_200_and_executes_zero_database_queries(
    api_client, django_assert_num_queries
) -> None:
    with django_assert_num_queries(0):
        response = api_client.get("/api/v1/health/live/")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_liveness_endpoint_is_unauthenticated(api_client) -> None:
    response = api_client.get("/api/v1/health/live/")
    assert response.status_code == 200
    assert response.status_code != 401
    assert response.status_code != 403


def test_liveness_endpoint_works_when_database_is_down(api_client) -> None:
    with patch("django.db.connection.ensure_connection", side_effect=DatabaseError("DB Down")):
        response = api_client.get("/api/v1/health/live/")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


@pytest.mark.django_db
def test_readiness_endpoint_healthy(api_client) -> None:
    response = api_client.get("/api/v1/health/ready/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["checks"]["database"]["status"] == "ok"
    assert payload["checks"]["migrations"]["status"] == "ok"


@pytest.mark.django_db
def test_readiness_endpoint_is_unauthenticated(api_client) -> None:
    response = api_client.get("/api/v1/health/ready/")
    assert response.status_code == 200
    assert response.status_code != 401
    assert response.status_code != 403


@pytest.mark.django_db
def test_readiness_endpoint_database_failure_returns_503_and_sanitizes(
    api_client, caplog
) -> None:
    sensitive_raw_error = (
        "FATAL: password authentication failed for user 'postgres_superuser' "
        "at server 10.150.0.12:5432; SELECT * FROM secret_table"
    )

    integration_logger = logging.getLogger("yara.integration")
    integration_logger.addHandler(caplog.handler)
    try:
        with caplog.at_level(logging.ERROR, logger="yara.integration"):
            with patch("django.db.connection.ensure_connection", side_effect=DatabaseError(sensitive_raw_error)):
                response = api_client.get("/api/v1/health/ready/")
    finally:
        integration_logger.removeHandler(caplog.handler)

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "unready"
    assert payload["checks"]["database"]["status"] == "error"
    assert payload["checks"]["database"]["detail"] == "Database connectivity check failed."
    assert payload["checks"]["migrations"]["status"] == "unavailable"
    assert payload["checks"]["migrations"]["detail"] == "Database unreachable."

    raw_response_text = response.content.decode("utf-8")
    assert "postgres_superuser" not in raw_response_text
    assert "10.150.0.12" not in raw_response_text
    assert "secret_table" not in raw_response_text
    assert "password" not in raw_response_text

    assert any("Database connectivity health probe failed" in record.message for record in caplog.records)


@pytest.mark.django_db
def test_readiness_endpoint_pending_migrations_returns_503_and_sanitizes(
    api_client, caplog
) -> None:
    integration_logger = logging.getLogger("yara.integration")
    integration_logger.addHandler(caplog.handler)
    try:
        with caplog.at_level(logging.WARNING, logger="yara.integration"):
            mock_plan = [("fake_app_1", "0002_migration"), ("fake_app_2", "0005_migration")]
            with patch("django.db.migrations.executor.MigrationExecutor.migration_plan", return_value=mock_plan):
                response = api_client.get("/api/v1/health/ready/")
    finally:
        integration_logger.removeHandler(caplog.handler)

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "unready"
    assert payload["checks"]["database"]["status"] == "ok"
    assert payload["checks"]["migrations"]["status"] == "error"
    assert payload["checks"]["migrations"]["detail"] == "2 unapplied migration(s) pending."

    assert any("Pending unapplied migrations detected: 2 migration(s) pending." in record.message for record in caplog.records)


@pytest.mark.django_db
def test_readiness_endpoint_migration_check_exception_sanitizes(
    api_client, caplog
) -> None:
    sensitive_internal_error = "OperationalError: relation 'django_migrations' does not exist in schema internal_secret"

    integration_logger = logging.getLogger("yara.integration")
    integration_logger.addHandler(caplog.handler)
    try:
        with caplog.at_level(logging.ERROR, logger="yara.integration"):
            with patch(
                "django.db.migrations.executor.MigrationExecutor.migration_plan",
                side_effect=Exception(sensitive_internal_error),
            ):
                response = api_client.get("/api/v1/health/ready/")
    finally:
        integration_logger.removeHandler(caplog.handler)

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "unready"
    assert payload["checks"]["database"]["status"] == "ok"
    assert payload["checks"]["migrations"]["status"] == "error"
    assert payload["checks"]["migrations"]["detail"] == "Migration readiness check failed."

    raw_response_text = response.content.decode("utf-8")
    assert "internal_secret" not in raw_response_text

    assert any("Migration readiness check failed" in record.message for record in caplog.records)
