"""Communication domain models."""

from __future__ import annotations

import uuid

from django.db import models

from domains.communication.enums import (
    CommunicationChannel,
    ContactStatus,
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
