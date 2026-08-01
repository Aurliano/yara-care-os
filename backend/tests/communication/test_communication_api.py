import pytest

from domains.communication.enums import CommunicationChannel


@pytest.mark.django_db
def test_create_contact_api(authenticated_client, licensed_elder):
    response = authenticated_client.post(
        f"/api/v1/elders/{licensed_elder.id}/contacts/",
        {
            "display_name": "API Contact",
            "phone": "+989129999999",
            "preferred_channel": CommunicationChannel.VOICE,
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["display_name"] == "API Contact"


@pytest.mark.django_db
def test_initiate_session_api(authenticated_client, licensed_elder, comm_user):
    contact_response = authenticated_client.post(
        f"/api/v1/elders/{licensed_elder.id}/contacts/",
        {
            "display_name": "Session Recipient",
            "preferred_channel": CommunicationChannel.VOICE,
        },
        format="json",
    )
    recipient_id = contact_response.json()["id"]
    response = authenticated_client.post(
        f"/api/v1/elders/{licensed_elder.id}/sessions/",
        {
            "channel": CommunicationChannel.VOICE,
            "recipient_contact_id": recipient_id,
            "initiator_user_id": str(comm_user.id),
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["status"] == "INITIATED"
