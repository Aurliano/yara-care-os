"""LiveKit WebRTC SFU adapter. Issues signed JWT join tokens locally.

The API key and secret never leave the Backend.
"""

from __future__ import annotations

import logging
import uuid
from datetime import timedelta
from typing import Any

import jwt
from django.conf import settings
from django.utils import timezone

from domains.communication.exceptions import CommunicationProviderError, ProviderFailureReason
from domains.communication.providers import ProviderLogin, ProviderRoom, ProviderUser

logger = logging.getLogger("yara.communication")


class LivekitCommunicationProvider:
    """Issue LiveKit room join tokens locally using API key and secret.

    LiveKit SFU creates rooms on-demand when participants connect with valid
    tokens. Token generation is a local CPU HMAC-SHA256 operation with zero
    outbound HTTP latency.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        api_secret: str | None = None,
        server_url: str | None = None,
    ) -> None:
        raw_key = api_key if api_key is not None else getattr(settings, "LIVEKIT_API_KEY", "")
        raw_secret = api_secret if api_secret is not None else getattr(settings, "LIVEKIT_API_SECRET", "")
        self._api_key = (raw_key or "").strip()
        self._api_secret = (raw_secret or "").strip()
        self._server_url = (
            server_url
            if server_url is not None
            else getattr(
                settings,
                "LIVEKIT_URL",
                "wss://livekit.yara.sayda.ir",
            )
        )

        if not self._api_key or not self._api_secret:
            logger.error("communication.livekit.provider.not_configured")
            raise CommunicationProviderError(
                "Communication provider is not configured.",
                reason=ProviderFailureReason.NOT_CONFIGURED,
            )

    def ensure_room(self, *, room_key: str, title: str) -> ProviderRoom:
        """Return a stable room identifier.

        LiveKit SFU rooms are auto-created when the first participant joins.
        """
        return ProviderRoom(key=room_key, external_id=room_key)

    def ensure_user(self, *, user_key: str, display_name: str) -> ProviderUser:
        """Return a stable participant identity."""
        return ProviderUser(key=user_key, external_id=user_key, display_name=display_name)

    def generate_login_url(
        self,
        *,
        room: ProviderRoom,
        user: ProviderUser,
        ttl_seconds: int,
    ) -> ProviderLogin:
        """Generate a time-limited signed LiveKit JWT join token."""
        now = timezone.now()
        expires_at = now + timedelta(seconds=ttl_seconds)
        now_ts = int(now.timestamp())
        exp_ts = int(expires_at.timestamp())

        payload: dict[str, Any] = {
            "iss": self._api_key,
            "sub": user.key,
            "iat": now_ts,
            "nbf": now_ts,
            "exp": exp_ts,
            "jti": str(uuid.uuid4()),
            "name": user.display_name or user.key,
            "video": {
                "room": room.key,
                "roomJoin": True,
                "canPublish": True,
                "canSubscribe": True,
                "canPublishData": True,
            },
        }

        try:
            token = jwt.encode(payload, self._api_secret, algorithm="HS256")
        except Exception as exc:
            logger.error("communication.livekit.token_encode_failed error=%s", exc)
            raise CommunicationProviderError(
                "Failed to generate communication join token.",
                reason=ProviderFailureReason.REJECTED,
            ) from exc

        return ProviderLogin(
            login_url=token,
            expires_at=expires_at,
        )

    def close_room(self, *, room: ProviderRoom) -> None:
        """Tear down room (no-op as LiveKit tears down empty rooms automatically)."""
        logger.info("communication.livekit.close_room room_key=%s", room.key)

    def api_key_fingerprint(self) -> str:
        """Diagnostics only: never reveals the key itself."""
        return f"length={len(self._api_key)} tail={self._api_key[-4:]}"
