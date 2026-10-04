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

# Deployment security settings matching production standards
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)  # noqa: F405
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])  # noqa: F405
