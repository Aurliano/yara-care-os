"""Operational environment and execution safety guards."""

from __future__ import annotations

import os

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import CommandError


def get_current_environment() -> str:
    """Return the active runtime environment identifier in lowercase.

    Canonical values: development | staging | production | test
    """
    env_val = getattr(settings, "YARA_ENVIRONMENT", None)
    if not env_val:
        env_val = os.environ.get("YARA_ENVIRONMENT", "development")
    return str(env_val).strip().lower()


def validate_database_environment(
    databases: dict | None = None,
    environment: str | None = None,
) -> None:
    """Validate that the active environment connects strictly to its authorized database.

    Enforces:
    1. If environment is 'staging', the default database NAME must be exactly 'yara_staging'.
       Connecting to 'yara', 'yara_test', or any other database in staging is strictly prohibited.
    2. In any non-production environment ('development', 'staging', 'test'), the default database
       NAME must never contain 'prod' or 'production'.
    3. If environment is 'production', the default database NAME must never be 'yara_staging',
       'yara_test', or 'yara'.

    Raises:
        ImproperlyConfigured: If any database isolation rule is violated.
    """
    env_name = (environment or get_current_environment()).lower()

    if databases is not None:
        db_config = databases.get("default", {})
    else:
        db_config = getattr(settings, "DATABASES", {}).get("default", {})

    db_name = str(db_config.get("NAME", "")).strip().lower()

    # Rule 1: Non-production environments must never touch a database named with prod/production
    if env_name != "production" and ("prod" in db_name or "production" in db_name):
        raise ImproperlyConfigured(
            f"CRITICAL DATABASE CONFIGURATION ERROR: Active environment is '{env_name}', "
            f"but database name '{db_name}' indicates a production database. Startup aborted."
        )

    # Rule 2: Staging must connect strictly and exclusively to 'yara_staging'
    if env_name == "staging":
        if db_name != "yara_staging":
            raise ImproperlyConfigured(
                f"CRITICAL DATABASE CONFIGURATION ERROR: Active environment is 'staging', "
                f"but connected database is '{db_name}'. Staging environment must connect "
                f"strictly and exclusively to database 'yara_staging'. Startup aborted."
            )

    # Rule 3: Production must never connect to dev/staging/test databases
    if env_name == "production":
        if db_name in {"yara", "yara_staging", "yara_test", "test_yara_test"}:
            raise ImproperlyConfigured(
                f"CRITICAL DATABASE CONFIGURATION ERROR: Active environment is 'production', "
                f"but connected database is non-production database '{db_name}'. Startup aborted."
            )


def ensure_not_production(
    command_name: str,
    *,
    require_confirmation: bool = False,
    is_confirmed: bool = False,
) -> None:
    """Enforce that destructive reset or seed management commands cannot run in production.

    Fails with CommandError if:
    1. YARA_ENVIRONMENT is 'production' (primary environment safety gate).
    2. Default database name contains 'prod' or 'production' (secondary defense-in-depth gate).
    3. require_confirmation is True and is_confirmed is False.

    Raises:
        CommandError: If the environment or database indicates production, or if required
                      confirmation is missing.
    """
    env_name = get_current_environment()
    if env_name == "production":
        raise CommandError(
            f"CRITICAL SAFETY CHECK FAILED: Refusing to execute '{command_name}' because active environment "
            f"is '{env_name}'. Destructive reset and test-data seed commands are strictly prohibited in "
            f"production environments."
        )

    db_name = str(settings.DATABASES.get("default", {}).get("NAME", "")).lower()
    if "prod" in db_name or "production" in db_name:
        raise CommandError(
            f"CRITICAL SAFETY CHECK FAILED: Refusing to execute '{command_name}'. "
            f"Database name '{db_name}' indicates a production database."
        )

    if require_confirmation and not is_confirmed:
        raise CommandError(
            f"Confirmation flag --confirm is required. "
            f"Usage: python manage.py {command_name} --confirm"
        )
