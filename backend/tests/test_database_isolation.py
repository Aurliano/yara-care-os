"""Tests for R2-A.3 Staging Database Isolation."""

import uuid

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import psycopg
import pytest

from common.guards import validate_database_environment


def _get_base_conn_params() -> dict:
    conn_params = settings.DATABASES["default"].copy()
    return {
        "user": conn_params.get("USER", "postgres"),
        "password": conn_params.get("PASSWORD", ""),
        "host": conn_params.get("HOST", "localhost") or "localhost",
        "port": int(conn_params.get("PORT", 5432) or 5432),
    }


def test_three_distinct_postgresql_databases_exist() -> None:
    """Verify yara, yara_staging, and yara_test are separate independent databases in PostgreSQL."""
    base_params = _get_base_conn_params()
    with psycopg.connect(dbname="postgres", **base_params) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT datname, oid FROM pg_database WHERE datname IN ('yara', 'yara_staging', 'yara_test')"
            )
            rows = cur.fetchall()

    databases = {row[0]: row[1] for row in rows}
    assert "yara" in databases, "Database 'yara' must exist"
    assert "yara_staging" in databases, "Database 'yara_staging' must exist"
    assert "yara_test" in databases, "Database 'yara_test' must exist"
    assert len(set(databases.values())) == 3, "Each database must have a unique PostgreSQL OID"


def test_validate_database_environment_staging_success() -> None:
    """When YARA_ENVIRONMENT=staging and database is yara_staging, validation succeeds."""
    staging_db = {"default": {"NAME": "yara_staging"}}
    validate_database_environment(databases=staging_db, environment="staging")


def test_validate_database_environment_staging_blocks_dev_database() -> None:
    """When YARA_ENVIRONMENT=staging and database is yara (dev), startup must fail."""
    dev_db = {"default": {"NAME": "yara"}}
    with pytest.raises(
        ImproperlyConfigured,
        match="Staging environment must connect strictly and exclusively to database 'yara_staging'",
    ):
        validate_database_environment(databases=dev_db, environment="staging")


def test_validate_database_environment_staging_blocks_production_database() -> None:
    """When YARA_ENVIRONMENT=staging and database has prod in name, startup must fail."""
    prod_db = {"default": {"NAME": "yara_production"}}
    with pytest.raises(ImproperlyConfigured, match="indicates a production database"):
        validate_database_environment(databases=prod_db, environment="staging")


def test_validate_database_environment_production_blocks_non_production_databases() -> None:
    """When YARA_ENVIRONMENT=production, connecting to yara or yara_staging must fail."""
    for forbidden_db in ("yara", "yara_staging", "yara_test"):
        db_config = {"default": {"NAME": forbidden_db}}
        with pytest.raises(ImproperlyConfigured, match="non-production database"):
            validate_database_environment(databases=db_config, environment="production")


def test_data_mutation_isolation_between_databases() -> None:
    """Writing a record to yara_staging must never affect yara or yara_test."""
    base_params = _get_base_conn_params()

    probe_phone = f"+98999{uuid.uuid4().hex[:7]}"
    probe_id = str(uuid.uuid4())
    probe_email = f"probe_{probe_id[:8]}@example.test"

    with psycopg.connect(dbname="yara_staging", **base_params) as conn_staging:
        with conn_staging.cursor() as cur:
            # Insert isolated probe into staging
            cur.execute(
                """
                INSERT INTO identity_user (id, phone, email, full_name, password, status, is_staff, is_superuser, created_at, updated_at)
                VALUES (%s, %s, %s, 'Staging Isolation Probe', 'unusable_pass', 'ACTIVE', false, false, NOW(), NOW())
                """,
                [probe_id, probe_phone, probe_email],
            )
            conn_staging.commit()

        try:
            # 1. Probe must exist in yara_staging
            with conn_staging.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM identity_user WHERE phone = %s", [probe_phone])
                assert cur.fetchone()[0] == 1, "Probe user must exist in yara_staging"

            # 2. Probe must NOT exist in yara (dev)
            with psycopg.connect(dbname="yara", **base_params) as conn_dev:
                with conn_dev.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM identity_user WHERE phone = %s", [probe_phone])
                    assert cur.fetchone()[0] == 0, "Probe user must NEVER appear in yara (dev)"

            # 3. Probe must NOT exist in yara_test / test_yara_test
            for test_db in ("test_yara_test", "yara_test"):
                try:
                    with psycopg.connect(dbname=test_db, **base_params) as conn_test:
                        with conn_test.cursor() as cur:
                            cur.execute(
                                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'identity_user')"
                            )
                            if cur.fetchone()[0]:
                                cur.execute("SELECT COUNT(*) FROM identity_user WHERE phone = %s", [probe_phone])
                                assert cur.fetchone()[0] == 0, f"Probe user must NEVER appear in {test_db}"
                except psycopg.OperationalError:
                    pass

        finally:
            # Clean up probe so yara_staging remains completely free of test data
            with conn_staging.cursor() as cur:
                cur.execute("DELETE FROM identity_user WHERE id = %s", [probe_id])
                conn_staging.commit()

    # Verify post-cleanup state in staging
    with psycopg.connect(dbname="yara_staging", **base_params) as conn_staging:
        with conn_staging.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM identity_user WHERE phone = %s", [probe_phone])
            assert cur.fetchone()[0] == 0, "Probe user must be deleted from yara_staging"
