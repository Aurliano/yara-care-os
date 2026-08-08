"""Development settings."""

from .base import *  # noqa: F403

DEBUG = True

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=[
        "localhost",
        "127.0.0.1",
        "[::1]",
        "10.0.2.2",  # Android emulator → host machine
    ],
)

# Hub tablets and other LAN clients reach the dev machine by private IP
# (e.g. http://192.168.1.101:8000). Django permits '*' only when DEBUG=True.
if env.bool("DEV_ALLOW_LAN_HOSTS", default=True):
    ALLOWED_HOSTS = list(dict.fromkeys([*ALLOWED_HOSTS, "*"]))

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8081",
    "http://127.0.0.1:8081",
]

LOG_LEVEL = "DEBUG"
