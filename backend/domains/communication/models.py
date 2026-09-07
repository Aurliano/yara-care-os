"""Communication domain models."""

from __future__ import annotations

import uuid
from datetime import datetime

from django.db import models
from django.utils import timezone

from domains.communication.enums import (
    CommunicationChannel,
    ContactStatus,
    MessageDirection,
    MessageStatus,
    MessageType,
    ParticipantRole,
    SessionOutcome,
    SessionStatus,
)


class Contact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    elder = models.ForeignKey(
        "identity_access.Elder",
        on_delete=models.PROTECT,
        related_name="contacts",
    )
    display_name = models.CharField(max_length=128)
    phone = models.CharField(max_length=32, blank=True, default="")
    communication_identities = models.JSONField(default=list)
    preferred_channel = models.CharField(
        max_length=16,
        choices=CommunicationChannel.choices,
        default=CommunicationChannel.VOICE,
    )
    photo_reference = models.UUIDField(null=True, blank=True)
    is_priority = models.BooleanField(default=False)
    status = models.CharField(
        max_length=16,
        choices=ContactStatus.choices,
        default=ContactStatus.ACTIVE,
    )
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "communication_contact"
        indexes = [
            models.Index(fields=["elder", "status"], name="comm_contact_elder_status_idx"),
            models.Index(fields=["elder", "is_priority"], name="comm_contact_priority_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.display_name}:{self.status}"


class CommunicationSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    elder = models.ForeignKey(
        "identity_access.Elder",
        on_delete=models.PROTECT,
        related_name="communication_sessions",
    )
    channel = models.CharField(max_length=16, choices=CommunicationChannel.choices)
    status = models.CharField(
        max_length=16,
        choices=SessionStatus.choices,
        default=SessionStatus.INITIATED,
    )
    outcome = models.CharField(max_length=16, choices=SessionOutcome.choices, blank=True, default="")
    initiated_at = models.DateTimeField()
    connected_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    external_execution_reference = models.UUIDField(null=True, blank=True)
    aggregate_version = models.PositiveBigIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "communication_session"
        indexes = [
            models.Index(fields=["elder", "initiated_at"], name="comm_session_elder_idx"),
            models.Index(fields=["status"], name="comm_session_status_idx"),
            models.Index(fields=["external_execution_reference"], name="comm_session_exec_ref_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.id}:{self.status}"


class SessionParticipant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    communication_session = models.ForeignKey(
        CommunicationSession,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="session_participations",
    )
    user_id = models.UUIDField(null=True, blank=True)
    role = models.CharField(max_length=16, choices=ParticipantRole.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "communication_session_participant"
        constraints = [
            models.UniqueConstraint(
                fields=["communication_session", "role"],
                name="comm_session_participant_unique_role",
            ),
        ]


class CallAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    communication_session = models.ForeignKey(
        CommunicationSession,
        on_delete=models.CASCADE,
        related_name="call_attempts",
    )
    attempt_number = models.PositiveIntegerField()
    outcome = models.CharField(max_length=16, blank=True, default="")
    failure_reason = models.CharField(max_length=255, blank=True, default="")
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "communication_call_attempt"
        constraints = [
            models.UniqueConstraint(
                fields=["communication_session", "attempt_number"],
                name="comm_call_attempt_unique_number",
            ),
        ]
        indexes = [
            models.Index(fields=["communication_session", "started_at"], name="comm_attempt_session_idx"),
        ]


class MessageAttachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file_path = models.CharField(max_length=512)
    file_size = models.PositiveBigIntegerField()
    mime_type = models.CharField(max_length=128)
    duration_seconds = models.FloatField(null=True, blank=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    original_filename = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "communication_message_attachment"

    def __str__(self) -> str:
        return f"{self.id}:{self.mime_type}"


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    elder = models.ForeignKey(
        "identity_access.Elder",
        on_delete=models.PROTECT,
        related_name="messages",
    )
    sender_user_id = models.UUIDField(null=True, blank=True)
    sender_contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_messages",
    )
    direction = models.CharField(max_length=16, choices=MessageDirection.choices)
    message_type = models.CharField(max_length=16, choices=MessageType.choices)
    body = models.TextField(blank=True, default="")
    attachment = models.OneToOneField(
        MessageAttachment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="message",
    )
    status = models.CharField(
        max_length=16,
        choices=MessageStatus.choices,
        default=MessageStatus.SENT,
    )
    idempotency_key = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "communication_message"
        indexes = [
            models.Index(fields=["elder", "-created_at"], name="comm_msg_elder_created_idx"),
            models.Index(fields=["elder", "status"], name="comm_msg_elder_status_idx"),
            models.Index(fields=["idempotency_key"], name="comm_msg_idempotency_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.id}:{self.direction}:{self.message_type}:{self.status}"


class MessageRecipient(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="recipients",
    )
    user_id = models.UUIDField(db_index=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "communication_message_recipient"
        constraints = [
            models.UniqueConstraint(
                fields=["message", "user_id"],
                name="comm_message_recipient_unique_user",
            ),
        ]
        indexes = [
            models.Index(fields=["message", "user_id"], name="comm_msg_recipient_idx"),
            models.Index(fields=["user_id", "delivered_at"], name="comm_msg_recip_deliv_idx"),
        ]

    def mark_delivered(self, timestamp: datetime | None = None) -> None:
        if self.delivered_at is None:
            self.delivered_at = timestamp or timezone.now()
            self.save(update_fields=["delivered_at"])

    def mark_read(self, timestamp: datetime | None = None) -> None:
        now = timestamp or timezone.now()
        update_fields = []
        if self.delivered_at is None:
            self.delivered_at = now
            update_fields.append("delivered_at")
        if self.read_at is None:
            self.read_at = now
            update_fields.append("read_at")
        if update_fields:
            self.save(update_fields=update_fields)

    def __str__(self) -> str:
        return f"{self.message_id}:{self.user_id}:read={self.read_at is not None}"

