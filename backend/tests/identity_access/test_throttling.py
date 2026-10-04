"""Regression test for authentication rate throttling."""

import pytest
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient

from common.throttling import AuthRegisterRateThrottle, AuthTokenRateThrottle


@pytest.mark.django_db
def test_auth_token_rate_throttling(monkeypatch):
    cache.clear()
    monkeypatch.setattr(AuthTokenRateThrottle, "get_rate", lambda self: "2/minute")
    client = APIClient()

    # 1st attempt
    r1 = client.post(
        "/api/v1/auth/token/",
        {"phone": "+989120000000", "password": "wrongpassword"},
        format="json",
    )
    assert r1.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED)

    # 2nd attempt
    r2 = client.post(
        "/api/v1/auth/token/",
        {"phone": "+989120000000", "password": "wrongpassword"},
        format="json",
    )
    assert r2.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED)

    # 3rd attempt should be throttled (429)
    r3 = client.post(
        "/api/v1/auth/token/",
        {"phone": "+989120000000", "password": "wrongpassword"},
        format="json",
    )
    assert r3.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.django_db
def test_auth_register_rate_throttling(monkeypatch):
    cache.clear()
    monkeypatch.setattr(AuthRegisterRateThrottle, "get_rate", lambda self: "2/minute")
    client = APIClient()

    client.post(
        "/api/v1/auth/register/",
        {"phone": "+989121111111", "password": "pass", "full_name": "Test"},
        format="json",
    )
    client.post(
        "/api/v1/auth/register/",
        {"phone": "+989121111112", "password": "pass", "full_name": "Test"},
        format="json",
    )
    r3 = client.post(
        "/api/v1/auth/register/",
        {"phone": "+989121111113", "password": "pass", "full_name": "Test"},
        format="json",
    )
    assert r3.status_code == status.HTTP_429_TOO_MANY_REQUESTS
