"""Communication call start/end/login-url API and room reuse tests."""

from __future__ import annotations

import pytest

from domains.communication.enums import CommunicationChannel, SessionStatus
from domains.communication.models import CommunicationSession
from domains.communication.services.contacts import create_contact
from infrastructure.communication.factory import reset_fake_provider
from infrastructure.communication.models import (
    ProviderCallBinding,
    ProviderRoomBinding,
    ProviderSubjectType,
    ProviderUserBinding,
)


@pytest.fixture(autouse=True)
def _reset_fake_provider():
    reset_fake_provider()
    yield
    reset_fake_provider()


def _start_payload(elder, contact):
    return {
        "elder_id": str(elder.id),
        "channel": CommunicationChannel.VOICE,
        "recipient_contact_id": str(contact.id),
    }


@pytest.mark.django_db
def test_call_start_returns_join_credentials(authenticated_client, licensed_elder, comm_user):
    contact = create_contact(
        elder_id=licensed_elder.id,
        display_name="Daughter",
        preferred_channel=CommunicationChannel.VOICE,
    )
    response = authenticated_client.post(
        "/api/v1/communication/call/start/",
        _start_payload(licensed_elder, contact),
        format="json",
    )
    assert response.status_code == 201
    body = response.json()
    assert set(body) >= {"roomId", "loginUrl", "expiresAt", "sessionId"}
    assert body["loginUrl"].startswith("https://example.test/join/")
    assert "skyroom" not in body["loginUrl"]
    assert "apikey" not in body["loginUrl"].lower()
    session = CommunicationSession.objects.get(pk=body["sessionId"])
    assert session.status == SessionStatus.CONNECTING
    assert ProviderRoomBinding.objects.filter(elder_id=licensed_elder.id).count() == 1
    assert ProviderCallBinding.objects.filter(communication_session_id=session.id).count() == 1


@pytest.mark.django_db
def test_second_call_start_reuses_room(authenticated_client, licensed_elder):
    contact = create_contact(
        elder_id=licensed_elder.id,
        display_name="Son",
        preferred_channel=CommunicationChannel.VOICE,
    )
    first = authenticated_client.post(
        "/api/v1/communication/call/start/",
        _start_payload(licensed_elder, contact),
        format="json",
    )
    second = authenticated_client.post(
        "/api/v1/communication/call/start/",
        _start_payload(licensed_elder, contact),
        format="json",
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["roomId"] == second.json()["roomId"]
    assert first.json()["sessionId"] != second.json()["sessionId"]
    assert ProviderRoomBinding.objects.filter(elder_id=licensed_elder.id).count() == 1
    assert CommunicationSession.objects.filter(elder_id=licensed_elder.id).count() == 2


@pytest.mark.django_db
def test_call_end_does_not_delete_room(authenticated_client, licensed_elder):
    contact = create_contact(
        elder_id=licensed_elder.id,
        display_name="Nurse",
        preferred_channel=CommunicationChannel.VOICE,
    )
    started = authenticated_client.post(
        "/api/v1/communication/call/start/",
        _start_payload(licensed_elder, contact),
        format="json",
    ).json()
    ended = authenticated_client.post(
        "/api/v1/communication/call/end/",
        {"session_id": started["sessionId"]},
        format="json",
    )
    assert ended.status_code == 200
    session = CommunicationSession.objects.get(pk=started["sessionId"])
    assert session.status == SessionStatus.CANCELLED
    assert ProviderRoomBinding.objects.filter(elder_id=licensed_elder.id).count() == 1


@pytest.mark.django_db
def test_login_url_reuses_room_without_new_session(authenticated_client, licensed_elder):
    contact = create_contact(
        elder_id=licensed_elder.id,
        display_name="Brother",
        preferred_channel=CommunicationChannel.VOICE,
    )
    authenticated_client.post(
        "/api/v1/communication/call/start/",
        _start_payload(licensed_elder, contact),
        format="json",
    )
    sessions_before = CommunicationSession.objects.filter(elder_id=licensed_elder.id).count()
    response = authenticated_client.post(
        "/api/v1/communication/login-url/",
        {"elder_id": str(licensed_elder.id)},
        format="json",
    )
    assert response.status_code == 200
    body = response.json()
    assert "loginUrl" in body
    assert "sessionId" not in body
    assert CommunicationSession.objects.filter(elder_id=licensed_elder.id).count() == sessions_before
    assert ProviderRoomBinding.objects.filter(elder_id=licensed_elder.id).count() == 1


@pytest.mark.django_db
def test_hub_login_url_uses_elder_hub_identity(authenticated_client, licensed_elder):
    contact = create_contact(
        elder_id=licensed_elder.id,
        display_name="Hub Contact",
        preferred_channel=CommunicationChannel.VOICE,
    )
    authenticated_client.post(
        "/api/v1/communication/call/start/",
        _start_payload(licensed_elder, contact),
        format="json",
    )
    response = authenticated_client.post(
        "/api/v1/communication/login-url/",
        {"elder_id": str(licensed_elder.id)},
        format="json",
        HTTP_X_REPLICA_ID="11111111-1111-1111-1111-111111111111",
    )
    assert response.status_code == 200
    assert ProviderUserBinding.objects.filter(
        subject_type=ProviderSubjectType.ELDER_HUB,
        subject_id=licensed_elder.id,
    ).exists()


@pytest.mark.django_db
def test_call_start_requires_authentication(api_client, licensed_elder):
    response = api_client.post(
        "/api/v1/communication/call/start/",
        {
            "elder_id": str(licensed_elder.id),
            "channel": CommunicationChannel.VOICE,
            "recipient_contact_id": "11111111-1111-1111-1111-111111111111",
        },
        format="json",
    )
    assert response.status_code in {401, 403}
