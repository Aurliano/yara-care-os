"""Test settings."""

from .base import *  # noqa: F403

DEBUG = False

SECRET_KEY = "test-secret-key-not-for-production"

DATABASES = {
    "default": env.db(
        "TEST_DATABASE_URL",
        default="postgres://yara:yara@localhost:5432/yara_test",
    )
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

LOGGING["root"]["level"] = "WARNING"  # noqa: F405
