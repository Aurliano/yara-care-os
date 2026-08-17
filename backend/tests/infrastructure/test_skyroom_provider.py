"""Skyroom adapter tests with mocked HTTP. No network, no real API key in errors."""

from __future__ import annotations

import json
import urllib.error
from unittest.mock import patch

import pytest

from domains.communication.exceptions import CommunicationProviderError
from domains.communication.providers import ProviderRoom, ProviderUser
from infrastructure.communication.skyroom import SkyroomCommunicationProvider

API_KEY = "apikey-test-secret-do-not-leak"


class _FakeHTTPResponse:
    def __init__(self, payload: dict, status: int = 200) -> None:
        self._payload = json.dumps(payload).encode("utf-8")
        self.status = status

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *args) -> None:
        return None


def _provider() -> SkyroomCommunicationProvider:
    return SkyroomCommunicationProvider(
        api_key=API_KEY,
        base_url="https://www.skyroom.online/skyroom/api",
    )


def test_ensure_room_creates_then_reuses():
    calls: list[dict] = []

    def fake_urlopen(request, timeout=15):
        payload = json.loads(request.data.decode("utf-8"))
        calls.append(payload)
        action = payload["action"]
        if action == "getRoom" and len([c for c in calls if c["action"] == "getRoom"]) == 1:
            return _FakeHTTPResponse({"ok": False, "error_code": 15, "error_message": "not found"})
        if action == "createRoom":
            assert payload["params"]["op_login_first"] is False
            return _FakeHTTPResponse({"ok": True, "result": 41})
        if action == "getRoom":
            return _FakeHTTPResponse({"ok": True, "result": {"id": 41, "name": "yara-elder-abc"}})
        raise AssertionError(action)

    adapter = _provider()
    with patch("infrastructure.communication.skyroom.urllib.request.urlopen", side_effect=fake_urlopen):
        first = adapter.ensure_room(room_key="yara-elder-abc", title="Elder")
        second = adapter.ensure_room(room_key="yara-elder-abc", title="Elder")

    assert first.external_id == "41"
    assert second.external_id == "41"
    assert [c["action"] for c in calls] == ["getRoom", "createRoom", "getRoom"]


def test_ensure_user_creates_then_reuses():
    calls: list[str] = []

    def fake_urlopen(request, timeout=15):
        payload = json.loads(request.data.decode("utf-8"))
        calls.append(payload["action"])
        if payload["action"] == "getUser" and calls.count("getUser") == 1:
            return _FakeHTTPResponse({"ok": False, "error_code": 15, "error_message": "not found"})
        if payload["action"] == "createUser":
            return _FakeHTTPResponse({"ok": True, "result": 9})
        if payload["action"] == "getUser":
            return _FakeHTTPResponse({"ok": True, "result": {"id": 9, "username": "yara-user-abc"}})
        raise AssertionError(payload["action"])

    adapter = _provider()
    with patch("infrastructure.communication.skyroom.urllib.request.urlopen", side_effect=fake_urlopen):
        first = adapter.ensure_user(user_key="yara-user-abc", display_name="Ali")
        second = adapter.ensure_user(user_key="yara-user-abc", display_name="Ali")

    assert first.external_id == second.external_id == "9"
    assert calls == ["getUser", "createUser", "getUser"]


def test_generate_login_url_ttl_and_no_api_key_in_url():
    def fake_urlopen(request, timeout=15):
        payload = json.loads(request.data.decode("utf-8"))
        if payload["action"] == "addUserRooms":
            return _FakeHTTPResponse({"ok": True, "result": 1})
        if payload["action"] == "createLoginUrl":
            assert payload["params"]["ttl"] == 120
            assert payload["params"]["language"] == "fa"
            assert payload["params"]["access"] == 3
            return _FakeHTTPResponse({"ok": True, "result": "https://www.skyroom.online/ch/join/token"})
        raise AssertionError(payload["action"])

    adapter = _provider()
    room = ProviderRoom(key="room", external_id="41")
    user = ProviderUser(key="user", external_id="9", display_name="Ali")
    with patch("infrastructure.communication.skyroom.urllib.request.urlopen", side_effect=fake_urlopen):
        login = adapter.generate_login_url(room=room, user=user, ttl_seconds=120)

    assert login.login_url.startswith("https://www.skyroom.online/")
    assert API_KEY not in login.login_url


def test_provider_error_does_not_include_api_key():
    def fake_urlopen(request, timeout=15):
        raise urllib.error.URLError(f"failed contacting {API_KEY}")

    adapter = _provider()
    with patch("infrastructure.communication.skyroom.urllib.request.urlopen", side_effect=fake_urlopen):
        with pytest.raises(CommunicationProviderError) as exc_info:
            adapter.ensure_room(room_key="room", title="Elder")

    assert API_KEY not in str(exc_info.value)


def test_skyroom_error_message_is_redacted():
    def fake_urlopen(request, timeout=15):
        return _FakeHTTPResponse(
            {"ok": False, "error_code": 11, "error_message": f"invalid key {API_KEY}"}
        )

    adapter = _provider()
    with patch("infrastructure.communication.skyroom.urllib.request.urlopen", side_effect=fake_urlopen):
        with pytest.raises(CommunicationProviderError) as exc_info:
            adapter.ensure_room(room_key="room", title="Elder")

    assert API_KEY not in str(exc_info.value)
    assert "[redacted]" in str(exc_info.value)


def test_close_room_deletes_vendor_room():
    def fake_urlopen(request, timeout=15):
        payload = json.loads(request.data.decode("utf-8"))
        assert payload == {"action": "deleteRoom", "params": {"room_id": 41}}
        return _FakeHTTPResponse({"ok": True, "result": 1})

    adapter = _provider()
    with patch("infrastructure.communication.skyroom.urllib.request.urlopen", side_effect=fake_urlopen):
        adapter.close_room(room=ProviderRoom(key="room", external_id="41"))
