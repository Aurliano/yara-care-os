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

from domains.communication.exceptions import CommunicationProviderError, ProviderFailureReason
from domains.communication.providers import ProviderLogin, ProviderRoom, ProviderUser

logger = logging.getLogger("yara.communication")

SKYROOM_NOT_FOUND = 15
SKYROOM_RATE_LIMITED_STATUS = 503
DEFAULT_ACCESS = 3
DEFAULT_MAX_USERS = 8
EXPECTED_API_KEY_LENGTH = 50


class SkyroomCommunicationProvider:
    """Create/reuse Skyroom rooms and issue login URLs.

    Per the Skyroom web-service docs, ``createLoginUrl`` needs neither a vendor
    user nor room access, so this adapter never creates Skyroom users.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        service_id: int | None = None,
    ) -> None:
        raw_key = api_key if api_key is not None else getattr(settings, "SKYROOM_API_KEY", "")
        self._api_key = (raw_key or "").strip()
        self._base_url = (
            base_url
            if base_url is not None
            else getattr(
                settings,
                "SKYROOM_API_BASE_URL",
                "https://www.skyroom.online/skyroom/api",
            )
        )
        self._service_id = service_id if service_id is not None else getattr(settings, "SKYROOM_SERVICE_ID", 0)
        if not self._api_key:
            logger.error("communication.provider.not_configured")
            raise CommunicationProviderError(
                "Communication provider is not configured.",
                reason=ProviderFailureReason.NOT_CONFIGURED,
            )
        if len(self._api_key) != EXPECTED_API_KEY_LENGTH:
            logger.warning(
                "communication.provider.api_key_unexpected_length length=%s expected=%s",
                len(self._api_key),
                EXPECTED_API_KEY_LENGTH,
            )

    def ensure_room(self, *, room_key: str, title: str) -> ProviderRoom:
        existing = self._try_get("getRoom", {"name": room_key})
        if existing is not None:
            return ProviderRoom(key=room_key, external_id=str(existing["id"]))

        params: dict[str, Any] = {
            "name": room_key,
            "title": title,
            "guest_login": False,
            "op_login_first": False,
            "max_users": DEFAULT_MAX_USERS,
        }
        if self._service_id:
            params["service_id"] = int(self._service_id)
        room_id = self._call("createRoom", params)
        return ProviderRoom(key=room_key, external_id=str(room_id))

    def ensure_user(self, *, user_key: str, display_name: str) -> ProviderUser:
        """Return a stable login identity without provisioning a Skyroom user.

        ``createLoginUrl`` accepts any number or space-free string as
        ``user_id``, so creating vendor users would only add failure points
        (user quotas, rate limits) without any benefit.
        """
        return ProviderUser(key=user_key, external_id="", display_name=display_name)

    def generate_login_url(
        self,
        *,
        room: ProviderRoom,
        user: ProviderUser,
        ttl_seconds: int,
    ) -> ProviderLogin:
        params = {
            "room_id": int(room.external_id),
            "user_id": user.key,
            "nickname": user.display_name or user.key,
            "access": DEFAULT_ACCESS,
            "concurrent": 1,
            "language": "fa",
            "ttl": ttl_seconds,
        }
        result = self._call("createLoginUrl", params)
        login_url = _coerce_login_url(result)
        if login_url is None:
            logger.error(
                "skyroom.create_login_url.invalid_result room_id=%s result_type=%s preview=%s",
                room.external_id,
                type(result).__name__,
                self._redact(_preview_result(result)),
            )
            raise CommunicationProviderError(
                "Provider did not return a login URL.",
                reason=ProviderFailureReason.INVALID_RESPONSE,
            )
        return ProviderLogin(
            login_url=login_url,
            expires_at=timezone.now() + timedelta(seconds=ttl_seconds),
        )

    def close_room(self, *, room: ProviderRoom) -> None:
        self._call("deleteRoom", {"room_id": int(room.external_id)})

    def list_services(self) -> list[dict[str, Any]]:
        """Diagnostics only: the active services a room can be created on."""
        result = self._call("getServices")
        if not isinstance(result, list):
            raise CommunicationProviderError(
                "Provider returned an unexpected payload.",
                reason=ProviderFailureReason.INVALID_RESPONSE,
            )
        return result

    def api_key_fingerprint(self) -> str:
        """Diagnostics only: never reveals the key itself."""
        return f"length={len(self._api_key)} tail={self._api_key[-4:]}"

    def _try_get(self, action: str, params: dict[str, Any]) -> dict[str, Any] | None:
        try:
            result = self._call(action, params)
        except CommunicationProviderError as exc:
            if getattr(exc, "error_code", None) == SKYROOM_NOT_FOUND:
                return None
            raise
        if not isinstance(result, dict):
            raise CommunicationProviderError(
                "Provider returned an unexpected payload.",
                reason=ProviderFailureReason.INVALID_RESPONSE,
            )
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
        except urllib.error.HTTPError as exc:
            # Skyroom answers application errors with HTTP 200, so any HTTP
            # error status is transport or rate limiting, never a domain result.
            logger.error(
                "skyroom.call.http_error action=%s status=%s body=%s",
                action,
                exc.code,
                self._redact(_error_body(exc)),
            )
            if exc.code == SKYROOM_RATE_LIMITED_STATUS:
                raise CommunicationProviderError(
                    "Communication provider is busy.",
                    reason=ProviderFailureReason.BUSY,
                ) from exc
            raise CommunicationProviderError(
                "Communication provider is unreachable.",
                reason=ProviderFailureReason.UNREACHABLE,
            ) from exc
        except urllib.error.URLError as exc:
            logger.error("skyroom.call.transport_error action=%s error=%s", action, exc.reason)
            raise CommunicationProviderError(
                "Communication provider is unreachable.",
                reason=ProviderFailureReason.UNREACHABLE,
            ) from exc

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error("skyroom.call.invalid_json action=%s body=%s", action, self._redact(raw[:200]))
            raise CommunicationProviderError(
                "Communication provider returned invalid JSON.",
                reason=ProviderFailureReason.INVALID_RESPONSE,
            ) from exc

        if not parsed.get("ok"):
            error_code = parsed.get("error_code")
            message = self._redact(parsed.get("error_message") or "Communication provider request failed.")
            log = logger.debug if error_code == SKYROOM_NOT_FOUND else logger.error
            log("skyroom.call.rejected action=%s error_code=%s message=%s", action, error_code, message)
            raise CommunicationProviderError(
                message,
                error_code=error_code,
                reason=ProviderFailureReason.REJECTED,
            )
        logger.debug("skyroom.call.ok action=%s", action)
        return parsed.get("result")

    def _redact(self, text: str) -> str:
        if self._api_key and self._api_key in text:
            return text.replace(self._api_key, "[redacted]")
        return text


def _coerce_login_url(result: Any) -> str | None:
    """Accept the documented string URL and the object/list shapes Skyroom also uses."""
    if isinstance(result, str) and result.strip():
        return result.strip()
    if isinstance(result, dict):
        for key in ("url", "login_url", "loginUrl", "href"):
            value = result.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    if isinstance(result, list) and result:
        return _coerce_login_url(result[0])
    return None


def _preview_result(result: Any) -> str:
    if result is None:
        return "null"
    if isinstance(result, dict):
        return ",".join(sorted(str(key) for key in result))
    if isinstance(result, list):
        return f"list:{len(result)}"
    text = str(result)
    return text[:80]


def _error_body(exc: urllib.error.HTTPError) -> str:
    try:
        return exc.read().decode("utf-8", errors="replace")[:200]
    except Exception:  # noqa: BLE001 - diagnostics must never mask the original error
        return ""
