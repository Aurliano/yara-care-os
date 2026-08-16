"""Skyroom REST adapter. The API key never leaves this module."""

from __future__ import annotations

import json
import logging
import secrets
import urllib.error
import urllib.request
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.utils import timezone

from domains.communication.exceptions import CommunicationProviderError
from domains.communication.providers import ProviderLogin, ProviderRoom, ProviderUser

logger = logging.getLogger("yara.communication")

SKYROOM_NOT_FOUND = 15
DEFAULT_ACCESS = 3
DEFAULT_MAX_USERS = 8


class SkyroomCommunicationProvider:
    """Create/reuse Skyroom rooms and users; issue login URLs."""

    def __init__(self, *, api_key: str | None = None, base_url: str | None = None) -> None:
        self._api_key = api_key if api_key is not None else getattr(settings, "SKYROOM_API_KEY", "")
        self._base_url = (
            base_url
            if base_url is not None
            else getattr(
                settings,
                "SKYROOM_API_BASE_URL",
                "https://www.skyroom.online/skyroom/api",
            )
        )
        if not self._api_key:
            raise CommunicationProviderError("Communication provider is not configured.")

    def ensure_room(self, *, room_key: str, title: str) -> ProviderRoom:
        existing = self._try_get("getRoom", {"name": room_key})
        if existing is not None:
            return ProviderRoom(key=room_key, external_id=str(existing["id"]))

        room_id = self._call(
            "createRoom",
            {
                "name": room_key,
                "title": title,
                "guest_login": False,
                "max_users": DEFAULT_MAX_USERS,
            },
        )
        return ProviderRoom(key=room_key, external_id=str(room_id))

    def ensure_user(self, *, user_key: str, display_name: str) -> ProviderUser:
        existing = self._try_get("getUser", {"username": user_key})
        if existing is not None:
            return ProviderUser(
                key=user_key,
                external_id=str(existing["id"]),
                display_name=display_name,
            )

        user_id = self._call(
            "createUser",
            {
                "username": user_key,
                "nickname": display_name or user_key,
                "password": secrets.token_urlsafe(16),
                "is_public": False,
            },
        )
        return ProviderUser(key=user_key, external_id=str(user_id), display_name=display_name)

    def generate_login_url(
        self,
        *,
        room: ProviderRoom,
        user: ProviderUser,
        ttl_seconds: int,
    ) -> ProviderLogin:
        try:
            self._call(
                "addUserRooms",
                {
                    "user_id": int(user.external_id),
                    "rooms": [{"room_id": int(room.external_id), "access": DEFAULT_ACCESS}],
                },
            )
        except CommunicationProviderError:
            logger.info("skyroom addUserRooms skipped; login URL will still be issued")

        login_url = self._call(
            "createLoginUrl",
            {
                "room_id": int(room.external_id),
                "user_id": user.key,
                "nickname": user.display_name or user.key,
                "access": DEFAULT_ACCESS,
                "concurrent": 1,
                "ttl": ttl_seconds,
            },
        )
        if not isinstance(login_url, str) or not login_url:
            raise CommunicationProviderError("Provider did not return a login URL.")
        return ProviderLogin(
            login_url=login_url,
            expires_at=timezone.now() + timedelta(seconds=ttl_seconds),
        )

    def close_room(self, *, room: ProviderRoom) -> None:
        self._call("deleteRoom", {"room_id": int(room.external_id)})

    def _try_get(self, action: str, params: dict[str, Any]) -> dict[str, Any] | None:
        try:
            result = self._call(action, params)
        except CommunicationProviderError as exc:
            if getattr(exc, "error_code", None) == SKYROOM_NOT_FOUND:
                return None
            raise
        if not isinstance(result, dict):
            raise CommunicationProviderError("Provider returned an unexpected payload.")
        return result

    def _call(self, action: str, params: dict[str, Any] | None = None) -> Any:
        payload: dict[str, Any] = {"action": action}
        if params:
            payload["params"] = params
        body = json.dumps(payload).encode("utf-8")
        url = f"{self._base_url.rstrip('/')}/{self._api_key}"
        request = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            raise CommunicationProviderError("Communication provider is unreachable.") from exc

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CommunicationProviderError("Communication provider returned invalid JSON.") from exc

        if not parsed.get("ok"):
            raise CommunicationProviderError(
                self._redact(parsed.get("error_message") or "Communication provider request failed."),
                error_code=parsed.get("error_code"),
            )
        return parsed.get("result")

    def _redact(self, text: str) -> str:
        if self._api_key and self._api_key in text:
            return text.replace(self._api_key, "[redacted]")
        return text
