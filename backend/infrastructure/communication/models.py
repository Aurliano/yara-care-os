"""Persistent provider room/user bindings. Not CommunicationSession columns."""

from __future__ import annotations

import uuid

from django.db import models


class ProviderSubjectType(models.TextChoices):
    USER = "USER", "Family user"
    ELDER_HUB = "ELDER_HUB", "Elder Hub"


class ProviderRoomBinding(models.Model):
    """One persistent provider room per Elder (per provider)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    elder_id = models.UUIDField()
    provider = models.CharField(max_length=32, default="skyroom")
    room_key = models.CharField(max_length=128)
    external_room_id = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "infrastructure_provider_room_binding"
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "elder_id"],
                name="infra_provider_room_elder_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["elder_id"], name="infra_provider_room_elder_idx"),
        ]


class ProviderUserBinding(models.Model):
    """One persistent provider user per Family User or Elder Hub identity."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.CharField(max_length=32, default="skyroom")
    subject_type = models.CharField(max_length=16, choices=ProviderSubjectType.choices)
    subject_id = models.UUIDField()
    user_key = models.CharField(max_length=128)
    external_user_id = models.CharField(max_length=64)
    display_name = models.CharField(max_length=128, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "infrastructure_provider_user_binding"
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "subject_type", "subject_id"],
                name="infra_provider_user_subject_uniq",
            ),
        ]


class ProviderCallBinding(models.Model):
    """Links a CommunicationSession to the provider room and user used for that call."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    communication_session_id = models.UUIDField(unique=True)
    room_binding = models.ForeignKey(
        ProviderRoomBinding,
        on_delete=models.PROTECT,
        related_name="call_bindings",
    )
    user_binding = models.ForeignKey(
        ProviderUserBinding,
        on_delete=models.PROTECT,
        related_name="call_bindings",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "infrastructure_provider_call_binding"
