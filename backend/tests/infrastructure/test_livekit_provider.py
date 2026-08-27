"""LiveKit adapter unit tests. Token generation, room lifecycle, and protocol conformance."""

from __future__ import annotations

import time
from datetime import timedelta

import jwt
import pytest
from django.test import override_settings
from django.utils import timezone

from domains.communication.exceptions import CommunicationProviderError, ProviderFailureReason
from domains.communication.providers import CommunicationProvider, ProviderRoom, ProviderUser
from infrastructure.communication.factory import get_communication_provider
from infrastructure.communication.livekit import LivekitCommunicationProvider

API_KEY = "devkey"
API_SECRET = "secret012345678901234567890123456789"
SERVER_URL = "wss://livekit.yara.sayda.ir"


def _provider() -> LivekitCommunicationProvider:
    return LivekitCommunicationProvider(
        api_key=API_KEY,
        api_secret=API_SECRET,
        server_url=SERVER_URL,
    )


def test_livekit_provider_satisfies_protocol():
    adapter = _provider()
    assert callable(getattr(adapter, "ensure_room", None))
    assert callable(getattr(adapter, "ensure_user", None))
    assert callable(getattr(adapter, "generate_login_url", None))
    assert callable(getattr(adapter, "close_room", None))


def test_ensure_room_returns_stable_room_id():
    adapter = _provider()
    first = adapter.ensure_room(room_key="yara-elder-abc", title="Elder Room")
    second = adapter.ensure_room(room_key="yara-elder-abc", title="Elder Room")

    assert first.key == "yara-elder-abc"
    assert first.external_id == "yara-elder-abc"
    assert second.key == "yara-elder-abc"
    assert second.external_id == "yara-elder-abc"


def test_ensure_user_returns_stable_identity():
    adapter = _provider()
    user = adapter.ensure_user(user_key="yara-user-caregiver", display_name="Zahra")

    assert user.key == "yara-user-caregiver"
    assert user.external_id == "yara-user-caregiver"
    assert user.display_name == "Zahra"


def test_generate_login_url_issues_valid_livekit_jwt():
    adapter = _provider()
    room = ProviderRoom(key="room-elder-123", external_id="room-elder-123")
    user = ProviderUser(key="user-hub-456", external_id="user-hub-456", display_name="Ali")

    ttl = 1800
    before = timezone.now()
    login = adapter.generate_login_url(room=room, user=user, ttl_seconds=ttl)
    after = timezone.now()

    assert login.expires_at >= before + timedelta(seconds=ttl)
    assert login.expires_at <= after + timedelta(seconds=ttl)

    # Decode and verify JWT token claims
    decoded = jwt.decode(
        login.login_url,
        API_SECRET,
        algorithms=["HS256"],
        options={"require": ["iss", "sub", "exp", "iat", "nbf", "jti"]},
    )

    assert decoded["iss"] == API_KEY
    assert decoded["sub"] == "user-hub-456"
    assert decoded["name"] == "Ali"
    assert "video" in decoded
    assert decoded["video"]["room"] == "room-elder-123"
    assert decoded["video"]["roomJoin"] is True
    assert decoded["video"]["canPublish"] is True
    assert decoded["video"]["canSubscribe"] is True
    assert decoded["video"]["canPublishData"] is True
    assert decoded["exp"] - decoded["iat"] == ttl


def test_generate_login_url_fallback_user_name_when_display_name_empty():
    adapter = _provider()
    room = ProviderRoom(key="room-1", external_id="room-1")
    user = ProviderUser(key="user-key-only", external_id="user-key-only", display_name="")

    login = adapter.generate_login_url(room=room, user=user, ttl_seconds=300)
    decoded = jwt.decode(login.login_url, API_SECRET, algorithms=["HS256"])

    assert decoded["name"] == "user-key-only"


def test_close_room_succeeds_without_error():
    adapter = _provider()
    room = ProviderRoom(key="room-1", external_id="room-1")
    adapter.close_room(room=room)


def test_missing_api_key_raises_not_configured():
    with pytest.raises(CommunicationProviderError) as exc_info:
        LivekitCommunicationProvider(api_key="", api_secret=API_SECRET)
    assert exc_info.value.reason == ProviderFailureReason.NOT_CONFIGURED


def test_missing_api_secret_raises_not_configured():
    with pytest.raises(CommunicationProviderError) as exc_info:
        LivekitCommunicationProvider(api_key=API_KEY, api_secret="")
    assert exc_info.value.reason == ProviderFailureReason.NOT_CONFIGURED


def test_whitespace_keys_raise_not_configured():
    with pytest.raises(CommunicationProviderError) as exc_info:
        LivekitCommunicationProvider(api_key="   ", api_secret="   ")
    assert exc_info.value.reason == ProviderFailureReason.NOT_CONFIGURED


@override_settings(
    COMMUNICATION_PROVIDER="livekit",
    LIVEKIT_API_KEY=API_KEY,
    LIVEKIT_API_SECRET=API_SECRET,
    LIVEKIT_URL=SERVER_URL,
)
def test_factory_resolves_livekit_provider():
    provider = get_communication_provider()
    assert isinstance(provider, LivekitCommunicationProvider)


def test_api_key_fingerprint_does_not_leak_full_key():
    adapter = _provider()
    fp = adapter.api_key_fingerprint()
    assert API_KEY not in fp or len(API_KEY) <= 4
    assert API_SECRET not in fp
