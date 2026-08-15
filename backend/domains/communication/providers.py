"""Provider-agnostic communication transport port.

Skyroom (or any successor) is an infrastructure adapter behind this protocol.
The Communication domain depends only on these types.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ProviderRoom:
    """A persistent vendor room. Identifiers are opaque to the domain."""

    key: str
    external_id: str


@dataclass(frozen=True, slots=True)
class ProviderUser:
    """A persistent vendor user. Identifiers are opaque to the domain."""

    key: str
    external_id: str
    display_name: str


@dataclass(frozen=True, slots=True)
class ProviderLogin:
    """Time-limited join credentials issued by the transport provider."""

    login_url: str
    expires_at: datetime


class CommunicationProvider(Protocol):
    """Port for creating/reusing rooms and users and issuing join URLs."""

    def ensure_room(self, *, room_key: str, title: str) -> ProviderRoom:
        """Create the room if missing; otherwise reuse it."""

    def ensure_user(self, *, user_key: str, display_name: str) -> ProviderUser:
        """Create the user if missing; otherwise reuse it."""

    def generate_login_url(
        self,
        *,
        room: ProviderRoom,
        user: ProviderUser,
        ttl_seconds: int,
    ) -> ProviderLogin:
        """Issue a time-limited login URL for this user into this room."""

    def close_room(self, *, room: ProviderRoom) -> None:
        """Tear down a room. Not used when ending a call."""
