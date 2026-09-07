"""Communication messaging domain service."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import BinaryIO

from django.db import transaction
from django.utils import timezone

from domains.communication.enums import MessageDirection, MessageStatus, MessageType
from domains.communication.exceptions import (
    AttachmentNotFoundError,
    AuthorizationDeniedError,
    InvalidMessageError,
    MessageNotFoundError,
)
from domains.communication.models import Contact, Message, MessageAttachment, MessageRecipient
from domains.communication.services.events import (
    emit_message_created,
    emit_message_delivered,
    emit_message_read,
)
from domains.communication.services.storage import save_media_file
from domains.identity_access.enums import MembershipStatus
from domains.identity_access.models import Elder, Membership, User


def create_message_attachment(
    *,
    file_obj: BinaryIO,
    media_type: str,
    claimed_mime_type: str | None = None,
    original_filename: str = "",
    duration_seconds: float | None = None,
    width: int | None = None,
    height: int | None = None,
) -> MessageAttachment:
    """Store media file on disk and create a MessageAttachment record."""
    stored = save_media_file(
        file_obj=file_obj,
        media_type=media_type,
        claimed_mime_type=claimed_mime_type,
        original_filename=original_filename,
    )
    attachment = MessageAttachment.objects.create(
        id=stored.attachment_id,
        file_path=stored.relative_path,
        file_size=stored.file_size,
        mime_type=stored.mime_type,
        duration_seconds=duration_seconds,
        width=width,
        height=height,
        original_filename=stored.original_filename,
    )
    return attachment


def get_attachment(*, attachment_id: uuid.UUID) -> MessageAttachment:
    """Retrieve an attachment by ID or raise AttachmentNotFoundError."""
    try:
        return MessageAttachment.objects.get(id=attachment_id)
    except MessageAttachment.DoesNotExist as exc:
        raise AttachmentNotFoundError(f"Attachment {attachment_id} not found.") from exc


def resolve_message_recipients(elder_id: uuid.UUID) -> list[uuid.UUID]:
    """Resolve active caregiver user IDs for an Elder."""
    return list(
        Membership.objects.filter(
            elder_id=elder_id,
            status=MembershipStatus.ACTIVE,
        ).values_list("user_id", flat=True)
    )


def send_message(
    *,
    elder_id: uuid.UUID,
    direction: str,
    message_type: str,
    body: str = "",
    sender_user: User | None = None,
    sender_contact_id: uuid.UUID | None = None,
    attachment_id: uuid.UUID | None = None,
    idempotency_key: str = "",
) -> Message:
    """Create and dispatch a message. Idempotent by elder + idempotency_key."""
    if idempotency_key:
        existing = (
            Message.objects.filter(
                elder_id=elder_id,
                idempotency_key=idempotency_key,
            )
            .select_related("attachment", "sender_contact")
            .prefetch_related("recipients")
            .first()
        )
        if existing:
            return existing

    # Validation
    if message_type == MessageType.TEXT:
        if not body or not body.strip():
            raise InvalidMessageError("Text message body cannot be empty.")
    elif message_type in {MessageType.VOICE, MessageType.IMAGE, MessageType.VIDEO}:
        if not attachment_id:
            raise InvalidMessageError(f"Attachment is required for {message_type} message.")

    attachment = None
    if attachment_id:
        attachment = get_attachment(attachment_id=attachment_id)

    sender_contact = None
    if sender_contact_id:
        try:
            sender_contact = Contact.objects.get(id=sender_contact_id, elder_id=elder_id)
        except Contact.DoesNotExist:
            sender_contact = None

    now = timezone.now()
    with transaction.atomic():
        message = Message.objects.create(
            elder_id=elder_id,
            sender_user_id=sender_user.id if sender_user else None,
            sender_contact=sender_contact,
            direction=direction,
            message_type=message_type,
            body=body.strip() if body else "",
            attachment=attachment,
            status=MessageStatus.SENT,
            idempotency_key=idempotency_key or "",
            sent_at=now,
        )
        recipient_user_ids = resolve_message_recipients(elder_id=elder_id)
        if recipient_user_ids:
            MessageRecipient.objects.bulk_create(
                [
                    MessageRecipient(message=message, user_id=uid)
                    for uid in set(recipient_user_ids)
                ]
            )

    emit_message_created(
        message_id=message.id,
        elder_id=elder_id,
        direction=direction,
        message_type=message_type,
        attachment_id=attachment.id if attachment else None,
    )
    return message


def mark_message_delivered(
    *,
    message_id: uuid.UUID,
    user_id: uuid.UUID | None = None,
) -> Message:
    """Mark a message as DELIVERED upon receipt by recipient device."""
    try:
        message = (
            Message.objects.select_related("attachment", "sender_contact")
            .prefetch_related("recipients")
            .get(id=message_id)
        )
    except Message.DoesNotExist as exc:
        raise MessageNotFoundError(f"Message {message_id} not found.") from exc

    if user_id is not None:
        recipient = None
        for r in message.recipients.all():
            if r.user_id == user_id:
                recipient = r
                break
        if recipient is None:
            raise AuthorizationDeniedError(
                f"User {user_id} is not an authorized recipient of message {message_id}."
            )
        now = timezone.now()
        if recipient.delivered_at is None:
            recipient.mark_delivered(timestamp=now)
            emit_message_delivered(message_id=message.id, delivered_at=now, user_id=user_id)
    else:
        now = timezone.now()
        emit_message_delivered(message_id=message.id, delivered_at=now)

    return message


def mark_message_read(
    *,
    message_id: uuid.UUID,
    user_id: uuid.UUID | None = None,
) -> Message:
    """Mark a message as READ when viewed/listened to by recipient."""
    try:
        message = (
            Message.objects.select_related("attachment", "sender_contact")
            .prefetch_related("recipients")
            .get(id=message_id)
        )
    except Message.DoesNotExist as exc:
        raise MessageNotFoundError(f"Message {message_id} not found.") from exc

    if user_id is not None:
        recipient = None
        for r in message.recipients.all():
            if r.user_id == user_id:
                recipient = r
                break
        if recipient is None:
            raise AuthorizationDeniedError(
                f"User {user_id} is not an authorized recipient of message {message_id}."
            )
        now = timezone.now()
        if recipient.read_at is None:
            recipient.mark_read(timestamp=now)
            emit_message_read(message_id=message.id, read_at=now, user_id=user_id)
    else:
        now = timezone.now()
        emit_message_read(message_id=message.id, read_at=now)

    return message


def get_message(*, message_id: uuid.UUID) -> Message:
    """Retrieve a single message by ID."""
    try:
        return (
            Message.objects.select_related("attachment", "sender_contact")
            .prefetch_related("recipients")
            .get(id=message_id)
        )
    except Message.DoesNotExist as exc:
        raise MessageNotFoundError(f"Message {message_id} not found.") from exc


def list_elder_messages(
    *,
    elder_id: uuid.UUID,
    since: datetime | None = None,
    limit: int = 50,
) -> list[Message]:
    """List messages for an elder, optionally filtered to those created after `since`."""
    qs = (
        Message.objects.filter(elder_id=elder_id)
        .select_related("attachment", "sender_contact")
        .prefetch_related("recipients")
    )
    if since is not None:
        if timezone.is_naive(since):
            since = timezone.make_aware(since, timezone.utc)
        qs = qs.filter(created_at__gt=since)
    return list(qs.order_by("-created_at")[:limit])

