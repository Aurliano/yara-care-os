"""Fake provider reuse tests without HTTP."""

from infrastructure.communication.fake import FakeCommunicationProvider


def test_fake_provider_reuses_room_and_user():
    provider = FakeCommunicationProvider()
    room1 = provider.ensure_room(room_key="elder-1", title="Elder")
    room2 = provider.ensure_room(room_key="elder-1", title="Elder")
    user1 = provider.ensure_user(user_key="user-1", display_name="Ali")
    user2 = provider.ensure_user(user_key="user-1", display_name="Ali")
    login = provider.generate_login_url(room=room1, user=user1, ttl_seconds=60)

    assert room1 == room2
    assert user1 == user2
    assert provider.create_room_calls == 1
    assert provider.create_user_calls == 1
    assert "join" in login.login_url
    provider.close_room(room=room1)
    assert provider.close_room_calls == 1
