"""Staging environment settings."""

import environ

from common.guards import validate_database_environment
from .base import *  # noqa: F403

DEBUG = False
YARA_ENVIRONMENT = "staging"

# Load .env.staging if present
staging_env_file = BASE_DIR / ".env.staging"  # noqa: F405
if staging_env_file.exists():
    environ.Env.read_env(staging_env_file, overwrite=True)

# Explicitly resolve the staging database connection.
# Default strictly targets yara_staging.
staging_db_raw = env(  # noqa: F405
    "STAGING_DATABASE_URL",
    default=env("DATABASE_URL", default="postgres://yara:yara@localhost:5432/yara_staging"),  # noqa: F405
)

DATABASES = {
    "default": env.db_url_config(staging_db_raw),  # noqa: F405
}

# Enforce database isolation guard immediately at configuration load time
validate_database_environment(DATABASES, YARA_ENVIRONMENT)
