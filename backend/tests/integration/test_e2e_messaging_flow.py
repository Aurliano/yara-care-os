"""Unmocked end-to-end integration test for messaging flow.

Verifies authentication, text messaging, media upload, voice messaging,
recipient delivery/read lifecycle, and permission enforcement against real database.
"""

from __future__ import annotations

import io
import uuid

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient

from domains.communication.enums import MessageDirection, MessageType
from domains.communication.models import Message, MessageRecipient
from domains.identity_access.enums import PermissionCode
from domains.identity_access.models import Elder, User
from domains.identity_access.services.authorization import can
from domains.identity_access.services.profiles import create_user
from integration.services.family_lab_seed import (
    FAMILY_CAREGIVER_PASSWORD,
    FAMILY_CAREGIVER_PHONE,
    ensure_family_lab_seed,
    get_family_lab_elder_id,
)


@pytest.mark.django_db
def test_e2e_messaging_lifecycle_unmocked():
    # 1. Seed fresh lab environment
    seed_result = ensure_family_lab_seed()
    elder_id = get_family_lab_elder_id()
    assert elder_id is not None

    caregiver = User.objects.get(phone=FAMILY_CAREGIVER_PHONE)
    elder = Elder.objects.get(id=elder_id)

    # Verify baseline permissions are automatically granted
    assert can(caregiver, PermissionCode.SEND_MESSAGE, elder) is True
    assert can(caregiver, PermissionCode.VIEW_MESSAGES, elder) is True

    client = APIClient()

    # 2. Authenticate caregiver via real token endpoint
    login_resp = client.post(
        "/api/v1/auth/token/",
        {"phone": FAMILY_CAREGIVER_PHONE, "password": FAMILY_CAREGIVER_PASSWORD},
        format="json",
    )
    assert login_resp.status_code == status.HTTP_200_OK
    tokens = login_resp.data
    assert "access" in tokens
    access_token = tokens["access"]

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    # 3. Send text message to elder
    text_payload = {
        "direction": MessageDirection.FAMILY_TO_HUB,
        "message_type": MessageType.TEXT,
        "body": "سلام بابا، داروهات رو خوردی؟",
        "idempotency_key": str(uuid.uuid4()),
    }
    send_text_resp = client.post(
        f"/api/v1/elders/{elder_id}/messages/",
        text_payload,
        format="json",
    )
    assert send_text_resp.status_code == status.HTTP_201_CREATED, send_text_resp.data
    text_msg_data = send_text_resp.data
    assert text_msg_data["body"] == text_payload["body"]
    assert text_msg_data["message_type"] == MessageType.TEXT
    assert text_msg_data["direction"] == MessageDirection.FAMILY_TO_HUB

    text_msg_id = text_msg_data["id"]
    recipient_count = MessageRecipient.objects.filter(message_id=text_msg_id).count()
    assert recipient_count >= 1

    # 4. Upload audio attachment
    # Create valid dummy m4a audio bytes
    audio_content = b"\x00\x00\x00\x1cftypM4A \x00\x00\x00\x00M4A mp42isom" + b"\x00" * 1024
    audio_file = SimpleUploadedFile(
        "voice_note.m4a",
        audio_content,
        content_type="audio/m4a",
    )
    upload_resp = client.post(
        "/api/v1/media/upload/",
        {
            "file": audio_file,
            "media_type": "VOICE",
            "duration_seconds": 5,
        },
        format="multipart",
    )
    assert upload_resp.status_code == status.HTTP_201_CREATED, upload_resp.data
    attachment_id = upload_resp.data["id"]
    assert attachment_id is not None

    # 5. Send voice message with attachment
    voice_payload = {
        "direction": MessageDirection.FAMILY_TO_HUB,
        "message_type": MessageType.VOICE,
        "attachment_id": attachment_id,
        "idempotency_key": str(uuid.uuid4()),
    }
    send_voice_resp = client.post(
        f"/api/v1/elders/{elder_id}/messages/",
        voice_payload,
        format="json",
    )
    assert send_voice_resp.status_code == status.HTTP_201_CREATED, send_voice_resp.data
    voice_msg_data = send_voice_resp.data
    assert voice_msg_data["message_type"] == MessageType.VOICE
    assert voice_msg_data["attachment"]["id"] == attachment_id

    voice_msg_id = voice_msg_data["id"]

    # 6. Retrieve message list
    list_resp = client.get(f"/api/v1/elders/{elder_id}/messages/")
    assert list_resp.status_code == status.HTTP_200_OK
    messages = list_resp.data
    msg_ids = [m["id"] for m in messages]
    assert text_msg_id in msg_ids
    assert voice_msg_id in msg_ids

    # 6.1 Download attachment via Authorization header
    dl_header_resp = client.get(f"/api/v1/media/{attachment_id}/download/")
    assert dl_header_resp.status_code == status.HTTP_200_OK
    assert dl_header_resp["Content-Type"] in {"audio/m4a", "audio/mp4"}

    # 6.2 Download attachment via query parameter ?token= (for mobile media players)
    unauth_client = APIClient()
    dl_token_resp = unauth_client.get(f"/api/v1/media/{attachment_id}/download/?token={access_token}")
    assert dl_token_resp.status_code == status.HTTP_200_OK
    assert dl_token_resp["Content-Type"] in {"audio/m4a", "audio/mp4"}

    # 6.3 Download without any credentials fails 401
    dl_noauth_resp = unauth_client.get(f"/api/v1/media/{attachment_id}/download/")
    assert dl_noauth_resp.status_code == status.HTTP_401_UNAUTHORIZED

    # 7. Delivery & Read state lifecycle
    deliv_resp = client.post(f"/api/v1/messages/{text_msg_id}/delivered/")
    assert deliv_resp.status_code == status.HTTP_200_OK

    read_resp = client.post(f"/api/v1/messages/{text_msg_id}/read/")
    assert read_resp.status_code == status.HTTP_200_OK
    assert read_resp.data["read"] is True

    # 8. Verify unauthorized stranger cannot send message to elder
    stranger = create_user(
        phone="+989129999999",
        password="strangerpassword123",
        full_name="Stranger",
    )
    stranger_token_resp = client.post(
        "/api/v1/auth/token/",
        {"phone": "+989129999999", "password": "strangerpassword123"},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {stranger_token_resp.data['access']}")
    unauth_send_resp = client.post(
        f"/api/v1/elders/{elder_id}/messages/",
        {"direction": "FAMILY_TO_HUB", "message_type": "TEXT", "body": "Hacked"},
        format="json",
    )
    assert unauth_send_resp.status_code == status.HTTP_403_FORBIDDEN
