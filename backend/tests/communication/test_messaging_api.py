"""Tests for communication messaging API."""

from __future__ import annotations

import io
import uuid
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from domains.communication.enums import MessageDirection, MessageStatus, MessageType
from domains.communication.models import Message, MessageAttachment
from domains.identity_access.enums import MembershipStatus, PermissionCode, RoleCode
from domains.identity_access.models import Elder, Membership, Permission, Role, RolePermission, User


@pytest.fixture
def auth_client():
    client = APIClient()
    return client


@pytest.fixture
def test_setup():
    user = User.objects.create_user(
        phone="+989121112233",
        email="caregiver@test.com",
        password="test-password-123",
        full_name="Caregiver Ali",
    )
    elder = Elder.objects.create(full_name="Elder Reza")

    # Set up role and permissions
    role, _ = Role.objects.get_or_create(code=RoleCode.CAREGIVER, defaults={"name": "Caregiver"})
    perm_send, _ = Permission.objects.get_or_create(
        code=PermissionCode.SEND_MESSAGE, defaults={"name": "Send Message"}
    )
    perm_view, _ = Permission.objects.get_or_create(
        code=PermissionCode.VIEW_MESSAGES, defaults={"name": "View Messages"}
    )
    perm_status, _ = Permission.objects.get_or_create(
        code=PermissionCode.VIEW_ELDER_STATUS, defaults={"name": "View Elder Status"}
    )
    RolePermission.objects.get_or_create(role=role, permission=perm_send)
    RolePermission.objects.get_or_create(role=role, permission=perm_view)
    RolePermission.objects.get_or_create(role=role, permission=perm_status)

    membership = Membership.objects.create(
        user=user,
        elder=elder,
        role=role,
        is_primary=True,
        status=MembershipStatus.ACTIVE,
    )
    return {"user": user, "elder": elder, "membership": membership}


@pytest.mark.django_db
def test_send_and_list_text_message(auth_client, test_setup):
    user = test_setup["user"]
    elder = test_setup["elder"]
    auth_client.force_authenticate(user=user)

    url = f"/api/v1/elders/{elder.id}/messages/"
    payload = {
        "direction": MessageDirection.FAMILY_TO_HUB,
        "message_type": MessageType.TEXT,
        "body": "سلام بابا جون، حالت چطوره؟",
        "idempotency_key": "msg-idem-1",
    }
    response = auth_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    data = response.data
    assert data["body"] == "سلام بابا جون، حالت چطوره؟"
    assert data["status"] == MessageStatus.SENT
    assert data["direction"] == MessageDirection.FAMILY_TO_HUB
    assert data["message_type"] == MessageType.TEXT

    # List messages
    list_res = auth_client.get(url)
    assert list_res.status_code == status.HTTP_200_OK
    assert len(list_res.data) == 1
    assert list_res.data[0]["id"] == data["id"]


@pytest.mark.django_db
def test_send_empty_text_message_fails(auth_client, test_setup):
    user = test_setup["user"]
    elder = test_setup["elder"]
    auth_client.force_authenticate(user=user)

    url = f"/api/v1/elders/{elder.id}/messages/"
    payload = {
        "direction": MessageDirection.FAMILY_TO_HUB,
        "message_type": MessageType.TEXT,
        "body": "   ",
    }
    response = auth_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_message_idempotency(auth_client, test_setup):
    user = test_setup["user"]
    elder = test_setup["elder"]
    auth_client.force_authenticate(user=user)

    url = f"/api/v1/elders/{elder.id}/messages/"
    payload = {
        "direction": MessageDirection.FAMILY_TO_HUB,
        "message_type": MessageType.TEXT,
        "body": "پیام تکراری",
        "idempotency_key": "unique-idem-token-123",
    }
    res1 = auth_client.post(url, payload, format="json")
    assert res1.status_code == status.HTTP_201_CREATED

    res2 = auth_client.post(url, payload, format="json")
    assert res2.status_code == status.HTTP_201_CREATED
    assert res1.data["id"] == res2.data["id"]
    assert Message.objects.filter(elder=elder).count() == 1


@pytest.mark.django_db
def test_media_upload_and_voice_message(auth_client, test_setup):
    user = test_setup["user"]
    elder = test_setup["elder"]
    auth_client.force_authenticate(user=user)

    # 1. Upload audio file
    fake_audio = io.BytesIO(b"RIFF....WAVEfmt ....data....fake-audio-bytes")
    fake_audio.name = "voice_note.m4a"

    upload_url = "/api/v1/media/upload/"
    upload_res = auth_client.post(
        upload_url,
        {
            "file": fake_audio,
            "media_type": MessageType.VOICE,
            "duration_seconds": 12.5,
        },
        format="multipart",
    )
    assert upload_res.status_code == status.HTTP_201_CREATED
    attachment_id = upload_res.data["id"]
    assert upload_res.data["mime_type"] in {"audio/m4a", "audio/mp4"}
    assert upload_res.data["duration_seconds"] == 12.5

    # 2. Send voice message referencing attachment
    msg_url = f"/api/v1/elders/{elder.id}/messages/"
    msg_res = auth_client.post(
        msg_url,
        {
            "direction": MessageDirection.HUB_TO_FAMILY,
            "message_type": MessageType.VOICE,
            "attachment_id": attachment_id,
            "body": "",
        },
        format="json",
    )
    assert msg_res.status_code == status.HTTP_201_CREATED
    msg_data = msg_res.data
    assert msg_data["message_type"] == MessageType.VOICE
    assert msg_data["attachment"]["id"] == attachment_id

    # 3. Download media
    download_url = f"/api/v1/media/{attachment_id}/download/"
    download_res = auth_client.get(download_url)
    assert download_res.status_code == status.HTTP_200_OK
    assert b"".join(download_res.streaming_content) == b"RIFF....WAVEfmt ....data....fake-audio-bytes"


@pytest.mark.django_db
def test_image_media_upload_for_profile_photo_and_missing_media_type_validation(auth_client, test_setup):
    """Verifies that image upload requires media_type and succeeds with valid JPEG."""
    user = test_setup["user"]
    auth_client.force_authenticate(user=user)

    upload_url = "/api/v1/media/upload/"
    fake_img = io.BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 32)
    fake_img.name = "contact_avatar.jpg"

    # 1. Missing media_type returns 400 Bad Request
    res_no_type = auth_client.post(
        upload_url,
        {"file": fake_img},
        format="multipart",
    )
    assert res_no_type.status_code == status.HTTP_400_BAD_REQUEST
    assert "media_type" in res_no_type.data

    # 2. Including media_type=IMAGE returns 201 Created and creates attachment
    fake_img.seek(0)
    res_ok = auth_client.post(
        upload_url,
        {
            "file": fake_img,
            "media_type": MessageType.IMAGE,
        },
        format="multipart",
    )
    assert res_ok.status_code == status.HTTP_201_CREATED
    assert res_ok.data["mime_type"] == "image/jpeg"
    assert res_ok.data["id"] is not None


@pytest.mark.django_db
def test_message_lifecycle_delivered_and_read(auth_client, test_setup):
    user = test_setup["user"]
    elder = test_setup["elder"]
    auth_client.force_authenticate(user=user)

    url = f"/api/v1/elders/{elder.id}/messages/"
    payload = {
        "direction": MessageDirection.FAMILY_TO_HUB,
        "message_type": MessageType.TEXT,
        "body": "سلام",
    }
    msg_res = auth_client.post(url, payload, format="json")
    msg_id = msg_res.data["id"]
    assert msg_res.data["status"] == MessageStatus.SENT

    # Mark DELIVERED
    deliv_url = f"/api/v1/messages/{msg_id}/delivered/"
    deliv_res = auth_client.post(deliv_url)
    assert deliv_res.status_code == status.HTTP_200_OK
    assert deliv_res.data["status"] == MessageStatus.DELIVERED
    assert deliv_res.data["delivered_at"] is not None

    # Mark READ
    read_url = f"/api/v1/messages/{msg_id}/read/"
    read_res = auth_client.post(read_url)
    assert read_res.status_code == status.HTTP_200_OK
    assert read_res.data["status"] == MessageStatus.READ
    assert read_res.data["read_at"] is not None


@pytest.mark.django_db
def test_unauthorized_user_cannot_send_or_view(auth_client, test_setup):
    elder = test_setup["elder"]
    stranger = User.objects.create_user(
        phone="+989350001122",
        email="stranger@test.com",
        password="test-password-123",
    )
    auth_client.force_authenticate(user=stranger)

    url = f"/api/v1/elders/{elder.id}/messages/"
    res_list = auth_client.get(url)
    assert res_list.status_code == status.HTTP_403_FORBIDDEN

    res_send = auth_client.post(
        url,
        {
            "direction": MessageDirection.FAMILY_TO_HUB,
            "message_type": MessageType.TEXT,
            "body": "Unauthorized text",
        },
        format="json",
    )
    assert res_send.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_list_messages_with_since_epoch_millis(auth_client, test_setup):
    user = test_setup["user"]
    elder = test_setup["elder"]
    auth_client.force_authenticate(user=user)

    url = f"/api/v1/elders/{elder.id}/messages/"

    # Message 1 created in past
    msg1 = Message.objects.create(
        elder_id=elder.id,
        sender_user_id=user.id,
        direction=MessageDirection.FAMILY_TO_HUB,
        message_type=MessageType.TEXT,
        body="Message 1 (old)",
        status=MessageStatus.SENT,
    )
    Message.objects.filter(id=msg1.id).update(created_at=timezone.now() - timedelta(minutes=10))

    # Cutoff time in epoch millis (5 minutes ago, in UTC)
    cutoff = timezone.now() - timedelta(minutes=5)
    cutoff_millis = int(cutoff.timestamp() * 1000)

    # Message 2 created recently (1 minute ago)
    msg2 = Message.objects.create(
        elder_id=elder.id,
        sender_user_id=user.id,
        direction=MessageDirection.FAMILY_TO_HUB,
        message_type=MessageType.TEXT,
        body="Message 2 (new)",
        status=MessageStatus.SENT,
    )
    Message.objects.filter(id=msg2.id).update(created_at=timezone.now() - timedelta(minutes=1))

    # GET with since in epoch millis
    res = auth_client.get(f"{url}?since={cutoff_millis}")
    assert res.status_code == status.HTTP_200_OK
    assert len(res.data) == 1
    assert res.data[0]["id"] == str(msg2.id)
    assert res.data[0]["body"] == "Message 2 (new)"


@pytest.mark.django_db
def test_list_messages_with_since_iso8601(auth_client, test_setup):
    user = test_setup["user"]
    elder = test_setup["elder"]
    auth_client.force_authenticate(user=user)

    url = f"/api/v1/elders/{elder.id}/messages/"

    msg1 = Message.objects.create(
        elder_id=elder.id,
        sender_user_id=user.id,
        direction=MessageDirection.FAMILY_TO_HUB,
        message_type=MessageType.TEXT,
        body="Message 1 (old)",
        status=MessageStatus.SENT,
    )
    Message.objects.filter(id=msg1.id).update(created_at=timezone.now() - timedelta(minutes=10))

    cutoff = timezone.now() - timedelta(minutes=5)
    cutoff_iso = cutoff.isoformat()

    msg2 = Message.objects.create(
        elder_id=elder.id,
        sender_user_id=user.id,
        direction=MessageDirection.FAMILY_TO_HUB,
        message_type=MessageType.TEXT,
        body="Message 2 (new)",
        status=MessageStatus.SENT,
    )
    Message.objects.filter(id=msg2.id).update(created_at=timezone.now() - timedelta(minutes=1))

    res = auth_client.get(f"{url}?since={cutoff_iso}")
    assert res.status_code == status.HTTP_200_OK
    assert len(res.data) == 1
    assert res.data[0]["id"] == str(msg2.id)


@pytest.mark.django_db
def test_list_messages_invalid_since_format(auth_client, test_setup):
    user = test_setup["user"]
    elder = test_setup["elder"]
    auth_client.force_authenticate(user=user)

    url = f"/api/v1/elders/{elder.id}/messages/?since=not-a-date"
    res = auth_client.get(url)
    assert res.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_message_sender_uses_contact_elder_facing_display_name(auth_client, test_setup):
    user = test_setup["user"]
    elder = test_setup["elder"]
    auth_client.force_authenticate(user=user)

    # 1. Without Contact, fallback to User full_name
    msg = Message.objects.create(
        elder_id=elder.id,
        sender_user_id=user.id,
        direction=MessageDirection.FAMILY_TO_HUB,
        message_type=MessageType.TEXT,
        body="سلام",
        status=MessageStatus.SENT,
    )
    url = f"/api/v1/elders/{elder.id}/messages/"
    res = auth_client.get(url)
    assert res.status_code == status.HTTP_200_OK
    assert res.data[0]["sender"]["display_name"] == "Caregiver Ali"

    # 2. Create elder-scoped Contact with elder-facing display_name (e.g. "پسر")
    from domains.communication.models import Contact
    contact = Contact.objects.create(
        elder=elder,
        display_name="پسر",
        phone=user.phone,
        communication_identities=[str(user.id)],
    )

    res2 = auth_client.get(url)
    assert res2.status_code == status.HTTP_200_OK
    assert res2.data[0]["sender"]["display_name"] == "پسر"

    # 3. Update Contact display name to "علی (پسرم)" and verify authoritative resolution
    contact.display_name = "علی (پسرم)"
    contact.save()

    res3 = auth_client.get(url)
    assert res3.status_code == status.HTTP_200_OK
    assert res3.data[0]["sender"]["display_name"] == "علی (پسرم)"

