"""Tests for multi-recipient messaging domain semantics and isolation."""

from __future__ import annotations

import uuid
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from domains.communication.enums import MessageDirection, MessageStatus, MessageType
from domains.communication.models import Message, MessageRecipient
from domains.communication.services.messaging import send_message
from domains.identity_access.enums import MembershipStatus, PermissionCode, RoleCode
from domains.identity_access.models import Elder, Membership, Permission, Role, RolePermission, User


@pytest.fixture
def multi_caregiver_setup():
    elder = Elder.objects.create(full_name="Elder Reza")

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

    # Caregiver A (Primary)
    user_a = User.objects.create_user(
        phone="+989121110001",
        email="caregiver_a@test.com",
        password="test-password-123",
        full_name="Caregiver A",
    )
    Membership.objects.create(
        user=user_a,
        elder=elder,
        role=role,
        is_primary=True,
        status=MembershipStatus.ACTIVE,
    )

    # Caregiver B
    user_b = User.objects.create_user(
        phone="+989121110002",
        email="caregiver_b@test.com",
        password="test-password-123",
        full_name="Caregiver B",
    )
    Membership.objects.create(
        user=user_b,
        elder=elder,
        role=role,
        is_primary=False,
        status=MembershipStatus.ACTIVE,
    )

    # Caregiver C
    user_c = User.objects.create_user(
        phone="+989121110003",
        email="caregiver_c@test.com",
        password="test-password-123",
        full_name="Caregiver C",
    )
    Membership.objects.create(
        user=user_c,
        elder=elder,
        role=role,
        is_primary=False,
        status=MembershipStatus.ACTIVE,
    )

    # Stranger (No membership with elder)
    stranger = User.objects.create_user(
        phone="+989129999999",
        email="stranger@test.com",
        password="test-password-123",
        full_name="Stranger",
    )

    return {
        "elder": elder,
        "caregiver_a": user_a,
        "caregiver_b": user_b,
        "caregiver_c": user_c,
        "stranger": stranger,
    }


@pytest.mark.django_db
def test_scenario_1_independent_delivery_state(multi_caregiver_setup):
    """Test 1: Caregiver A marking delivered does not alter Caregiver B's delivery state."""
    elder = multi_caregiver_setup["elder"]
    user_a = multi_caregiver_setup["caregiver_a"]
    user_b = multi_caregiver_setup["caregiver_b"]

    msg = send_message(
        elder_id=elder.id,
        direction=MessageDirection.HUB_TO_FAMILY,
        message_type=MessageType.TEXT,
        body="پیام آزمایشی هاب",
    )

    client_a = APIClient()
    client_a.force_authenticate(user=user_a)

    deliv_url = f"/api/v1/messages/{msg.id}/delivered/"
    res_a = client_a.post(deliv_url)
    assert res_a.status_code == status.HTTP_200_OK
    assert res_a.data["status"] == MessageStatus.DELIVERED
    assert res_a.data["delivered"] is True
    assert res_a.data["delivered_at"] is not None

    recip_a = MessageRecipient.objects.get(message=msg, user_id=user_a.id)
    recip_b = MessageRecipient.objects.get(message=msg, user_id=user_b.id)

    assert recip_a.delivered_at is not None
    assert recip_b.delivered_at is None


@pytest.mark.django_db
def test_scenario_2_independent_read_state(multi_caregiver_setup):
    """Test 2: Caregiver A marking read sets A to READ, while B remains SENT/unread."""
    elder = multi_caregiver_setup["elder"]
    user_a = multi_caregiver_setup["caregiver_a"]
    user_b = multi_caregiver_setup["caregiver_b"]

    msg = send_message(
        elder_id=elder.id,
        direction=MessageDirection.HUB_TO_FAMILY,
        message_type=MessageType.TEXT,
        body="پیام بررسی وضعیت خواندن",
    )

    client_a = APIClient()
    client_a.force_authenticate(user=user_a)

    read_url = f"/api/v1/messages/{msg.id}/read/"
    res_a = client_a.post(read_url)
    assert res_a.status_code == status.HTTP_200_OK
    assert res_a.data["status"] == MessageStatus.READ
    assert res_a.data["read"] is True
    assert res_a.data["read_at"] is not None
    assert res_a.data["delivered"] is True

    recip_a = MessageRecipient.objects.get(message=msg, user_id=user_a.id)
    recip_b = MessageRecipient.objects.get(message=msg, user_id=user_b.id)

    assert recip_a.read_at is not None
    assert recip_b.read_at is None
    assert recip_b.delivered_at is None


@pytest.mark.django_db
def test_scenario_3_history_isolation(multi_caregiver_setup):
    """Test 3: History endpoint GET /elders/{id}/messages/ returns isolated states to each caregiver."""
    elder = multi_caregiver_setup["elder"]
    user_a = multi_caregiver_setup["caregiver_a"]
    user_b = multi_caregiver_setup["caregiver_b"]

    msg = send_message(
        elder_id=elder.id,
        direction=MessageDirection.HUB_TO_FAMILY,
        message_type=MessageType.TEXT,
        body="پیام ایزولاسیون تاریخچه",
    )

    client_a = APIClient()
    client_a.force_authenticate(user=user_a)
    client_b = APIClient()
    client_b.force_authenticate(user=user_b)

    # A marks delivered and read
    client_a.post(f"/api/v1/messages/{msg.id}/read/")

    history_url = f"/api/v1/elders/{elder.id}/messages/"

    # History view for A
    res_history_a = client_a.get(history_url)
    assert res_history_a.status_code == status.HTTP_200_OK
    msg_a = res_history_a.data[0]
    assert msg_a["id"] == str(msg.id)
    assert msg_a["status"] == MessageStatus.READ
    assert msg_a["read"] is True
    assert msg_a["delivered"] is True
    assert msg_a["read_at"] is not None
    assert msg_a["delivered_at"] is not None

    # History view for B (must NOT reflect A's delivery or read)
    res_history_b = client_b.get(history_url)
    assert res_history_b.status_code == status.HTTP_200_OK
    msg_b = res_history_b.data[0]
    assert msg_b["id"] == str(msg.id)
    assert msg_b["status"] == MessageStatus.SENT
    assert msg_b["read"] is False
    assert msg_b["delivered"] is False
    assert msg_b["read_at"] is None
    assert msg_b["delivered_at"] is None

    # Now B marks delivered
    client_b.post(f"/api/v1/messages/{msg.id}/delivered/")
    res_history_b_after = client_b.get(history_url)
    msg_b_after = res_history_b_after.data[0]
    assert msg_b_after["status"] == MessageStatus.DELIVERED
    assert msg_b_after["delivered"] is True
    assert msg_b_after["read"] is False

    # A's history remains READ
    res_history_a_after = client_a.get(history_url)
    assert res_history_a_after.data[0]["status"] == MessageStatus.READ


@pytest.mark.django_db
def test_scenario_4_unauthorized_recipient_rejected(multi_caregiver_setup):
    """Test 4: Non-recipient (stranger) receives HTTP 403 when attempting delivered/read."""
    elder = multi_caregiver_setup["elder"]
    stranger = multi_caregiver_setup["stranger"]

    msg = send_message(
        elder_id=elder.id,
        direction=MessageDirection.HUB_TO_FAMILY,
        message_type=MessageType.TEXT,
        body="پیام محرمانه خانواده",
    )

    client_stranger = APIClient()
    client_stranger.force_authenticate(user=stranger)

    deliv_res = client_stranger.post(f"/api/v1/messages/{msg.id}/delivered/")
    assert deliv_res.status_code == status.HTTP_403_FORBIDDEN

    read_res = client_stranger.post(f"/api/v1/messages/{msg.id}/read/")
    assert read_res.status_code == status.HTTP_403_FORBIDDEN

    # Verify no recipient was created or altered for stranger
    assert not MessageRecipient.objects.filter(message=msg, user_id=stranger.id).exists()


@pytest.mark.django_db
def test_scenario_5_multiple_recipients_three_caregivers(multi_caregiver_setup):
    """Test 5: Three active caregivers track independent lifecycles on the same message."""
    elder = multi_caregiver_setup["elder"]
    user_a = multi_caregiver_setup["caregiver_a"]
    user_b = multi_caregiver_setup["caregiver_b"]
    user_c = multi_caregiver_setup["caregiver_c"]

    msg = send_message(
        elder_id=elder.id,
        direction=MessageDirection.HUB_TO_FAMILY,
        message_type=MessageType.TEXT,
        body="پیام به سه مراقب",
    )

    recipients = MessageRecipient.objects.filter(message=msg)
    assert recipients.count() == 3
    recipient_user_ids = {r.user_id for r in recipients}
    assert recipient_user_ids == {user_a.id, user_b.id, user_c.id}

    client_a = APIClient()
    client_a.force_authenticate(user=user_a)
    client_b = APIClient()
    client_b.force_authenticate(user=user_b)
    client_c = APIClient()
    client_c.force_authenticate(user=user_c)

    # A marks delivered
    client_a.post(f"/api/v1/messages/{msg.id}/delivered/")

    # B marks delivered and read
    client_b.post(f"/api/v1/messages/{msg.id}/read/")

    # C performs no actions

    history_url = f"/api/v1/elders/{elder.id}/messages/"

    res_a = client_a.get(history_url).data[0]
    res_b = client_b.get(history_url).data[0]
    res_c = client_c.get(history_url).data[0]

    # Caregiver A: Delivered, unread
    assert res_a["status"] == MessageStatus.DELIVERED
    assert res_a["delivered"] is True
    assert res_a["read"] is False

    # Caregiver B: Delivered, read
    assert res_b["status"] == MessageStatus.READ
    assert res_b["delivered"] is True
    assert res_b["read"] is True

    # Caregiver C: Sent, unread, undelivered
    assert res_c["status"] == MessageStatus.SENT
    assert res_c["delivered"] is False
    assert res_c["read"] is False
