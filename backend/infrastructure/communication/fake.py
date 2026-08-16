"""In-memory CommunicationProvider for tests and local development."""

from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from domains.communication.exceptions import CommunicationProviderError
from domains.communication.providers import ProviderLogin, ProviderRoom, ProviderUser


class FakeCommunicationProvider:
    """Create/reuse rooms and users without calling a vendor."""

    def __init__(self) -> None:
        self.rooms: dict[str, ProviderRoom] = {}
        self.users: dict[str, ProviderUser] = {}
        self.create_room_calls = 0
        self.create_user_calls = 0
        self.login_url_calls = 0
        self.close_room_calls = 0
        self._next_room_id = 1
        self._next_user_id = 1

    def ensure_room(self, *, room_key: str, title: str) -> ProviderRoom:
        existing = self.rooms.get(room_key)
        if existing is not None:
            return existing
        self.create_room_calls += 1
        room = ProviderRoom(key=room_key, external_id=str(self._next_room_id))
        self._next_room_id += 1
        self.rooms[room_key] = room
        return room

    def ensure_user(self, *, user_key: str, display_name: str) -> ProviderUser:
        existing = self.users.get(user_key)
        if existing is not None:
            return existing
        self.create_user_calls += 1
        user = ProviderUser(
            key=user_key,
            external_id=str(self._next_user_id),
            display_name=display_name,
        )
        self._next_user_id += 1
        self.users[user_key] = user
        return user

    def generate_login_url(
        self,
        *,
        room: ProviderRoom,
        user: ProviderUser,
        ttl_seconds: int,
    ) -> ProviderLogin:
        self.login_url_calls += 1
        return ProviderLogin(
            login_url=f"https://example.test/join/{room.external_id}/{user.external_id}",
            expires_at=timezone.now() + timedelta(seconds=ttl_seconds),
        )

    def close_room(self, *, room: ProviderRoom) -> None:
        self.close_room_calls += 1
        self.rooms.pop(room.key, None)


def require_fake_provider(provider: object) -> FakeCommunicationProvider:
    if not isinstance(provider, FakeCommunicationProvider):
        raise CommunicationProviderError("Expected fake communication provider.")
    return provider
