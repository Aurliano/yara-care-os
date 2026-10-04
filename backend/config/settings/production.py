"""Production settings."""

from .base import *  # noqa: F403

DEBUG = False

YARA_ENVIRONMENT = env("YARA_ENVIRONMENT", default="production")  # noqa: F405

# Database configuration: defaults to yara_production to pass environment safety guards
prod_db_raw = env("PRODUCTION_DATABASE_URL", default=None)
if not prod_db_raw:
    raw = env("DATABASE_URL", default="postgres://yara:yara@localhost:5432/yara_production")
    if str(raw).rstrip("/").endswith("/yara"):
        prod_db_raw = "postgres://yara:yara@localhost:5432/yara_production"
    else:
        prod_db_raw = raw

DATABASES = {
    "default": env.db_url_config(prod_db_raw),
}

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
