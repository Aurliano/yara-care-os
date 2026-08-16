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
    assert set(body) == {"sessionId", "joinToken", "expiresAt"}
    assert body["joinToken"].startswith("https://example.test/join/")
    assert "skyroom" not in body["joinToken"]
    assert "apikey" not in body["joinToken"].lower()
    assert "loginUrl" not in body
    assert "roomId" not in body
    session = CommunicationSession.objects.get(pk=body["sessionId"])
    assert session.status == SessionStatus.CONNECTING
    assert ProviderRoomBinding.objects.filter(elder_id=licensed_elder.id).count() == 1
    assert ProviderCallBinding.objects.filter(communication_session_id=session.id).count() == 1


@pytest.mark.django_db
def test_second_call_start_conflicts_while_active(authenticated_client, licensed_elder):
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
    assert second.status_code == 409
    assert ProviderRoomBinding.objects.filter(elder_id=licensed_elder.id).count() == 1
    assert CommunicationSession.objects.filter(elder_id=licensed_elder.id).count() == 1


@pytest.mark.django_db
def test_call_start_after_end_reuses_room(authenticated_client, licensed_elder):
    contact = create_contact(
        elder_id=licensed_elder.id,
        display_name="Daughter",
        preferred_channel=CommunicationChannel.VOICE,
    )
    first = authenticated_client.post(
        "/api/v1/communication/call/start/",
        _start_payload(licensed_elder, contact),
        format="json",
    ).json()
    authenticated_client.post(
        "/api/v1/communication/call/end/",
        {"session_id": first["sessionId"]},
        format="json",
    )
    second = authenticated_client.post(
        "/api/v1/communication/call/start/",
        _start_payload(licensed_elder, contact),
        format="json",
    )
    assert second.status_code == 201
    assert second.json()["sessionId"] != first["sessionId"]
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
    assert "joinToken" in body
    assert "loginUrl" not in body
    assert "roomId" not in body
    assert body.get("sessionId") is not None
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


@pytest.mark.django_db
def test_unjoined_session_auto_cancels_after_timeout(licensed_elder, comm_user):
    from datetime import timedelta

    from django.utils import timezone

    from domains.communication.services.sessions import auto_cancel_unjoined_sessions, initiate_session

    contact = create_contact(
        elder_id=licensed_elder.id,
        display_name="Timeout Contact",
        preferred_channel=CommunicationChannel.VOICE,
    )
    session = initiate_session(
        elder_id=licensed_elder.id,
        channel=CommunicationChannel.VOICE,
        initiator_user_id=comm_user.id,
        recipient_contact_id=contact.id,
    )
    CommunicationSession.objects.filter(pk=session.id).update(
        initiated_at=timezone.now() - timedelta(minutes=3),
    )
    cancelled = auto_cancel_unjoined_sessions(timeout_seconds=120)
    session.refresh_from_db()
    assert cancelled == 1
    assert session.status == SessionStatus.CANCELLED


@pytest.mark.django_db
def test_integration_cycle_reports_communication_timeouts(licensed_elder, comm_user):
    from datetime import timedelta

    from django.utils import timezone

    from domains.communication.services.sessions import initiate_session
    from integration.context import IntegrationContext
    from integration.runtime.scheduler import run_integration_cycle

    contact = create_contact(
        elder_id=licensed_elder.id,
        display_name="Cycle Timeout",
        preferred_channel=CommunicationChannel.VOICE,
    )
    session = initiate_session(
        elder_id=licensed_elder.id,
        channel=CommunicationChannel.VOICE,
        initiator_user_id=comm_user.id,
        recipient_contact_id=contact.id,
    )
    CommunicationSession.objects.filter(pk=session.id).update(
        initiated_at=timezone.now() - timedelta(minutes=3),
    )
    result = run_integration_cycle(IntegrationContext())
    session.refresh_from_db()
    assert "communication_timeouts" in result
    assert result["communication_timeouts"] == 1
    assert session.status == SessionStatus.CANCELLED


def test_hub_sources_do_not_call_skyroom_rest():
    from pathlib import Path

    hub_root = Path(__file__).resolve().parents[3] / "apps" / "hub"
    forbidden = ("skyroom.online/skyroom/api", "skyroom_api_key", "apikey-")
    hits = []
    for path in hub_root.rglob("*.kt"):
        if "src" not in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for token in forbidden:
            if token in text:
                hits.append(f"{path.relative_to(hub_root)}:{token}")
    assert hits == []
