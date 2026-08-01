"""Contact aggregate commands and queries."""

from __future__ import annotations

import uuid
from typing import Any

from django.db import transaction
from django.utils import timezone

from domains.communication.enums import ContactStatus
from domains.communication.exceptions import ContactNotFoundError, InvalidContactStateError
from domains.communication.models import Contact
from domains.communication.services.events import (
    emit_contact_archived,
    emit_contact_created,
    emit_contact_updated,
)
from domains.identity_access.models import Elder


def _ensure_elder_exists(elder_id: uuid.UUID) -> Elder:
    try:
        return Elder.objects.get(pk=elder_id)
    except Elder.DoesNotExist as exc:
        raise InvalidContactStateError("Elder not found.") from exc


def get_contact(contact_id: uuid.UUID) -> Contact:
    try:
        return Contact.objects.get(pk=contact_id)
    except Contact.DoesNotExist as exc:
        raise ContactNotFoundError("Contact not found.") from exc


def get_elder_contacts(*, elder_id: uuid.UUID, include_archived: bool = False) -> list[Contact]:
    queryset = Contact.objects.filter(elder_id=elder_id)
    if not include_archived:
        queryset = queryset.filter(status=ContactStatus.ACTIVE)
    return list(queryset.order_by("display_name"))


def get_priority_contacts(*, elder_id: uuid.UUID) -> list[Contact]:
    return list(
        Contact.objects.filter(
            elder_id=elder_id,
            status=ContactStatus.ACTIVE,
            is_priority=True,
        ).order_by("display_name")
    )


@transaction.atomic
def create_contact(
    *,
    elder_id: uuid.UUID,
    display_name: str,
    phone: str = "",
    communication_identities: list[dict[str, Any]] | None = None,
    preferred_channel: str,
    photo_reference: uuid.UUID | None = None,
) -> Contact:
    _ensure_elder_exists(elder_id)
    contact = Contact.objects.create(
        elder_id=elder_id,
        display_name=display_name,
        phone=phone,
        communication_identities=communication_identities or [],
        preferred_channel=preferred_channel,
        photo_reference=photo_reference,
    )
    emit_contact_created(contact_id=contact.id, elder_id=elder_id)
    return contact


@transaction.atomic
def update_contact(
    contact_id: uuid.UUID,
    *,
    display_name: str | None = None,
    phone: str | None = None,
    communication_identities: list[dict[str, Any]] | None = None,
    preferred_channel: str | None = None,
    photo_reference: uuid.UUID | None = None,
) -> Contact:
    contact = Contact.objects.select_for_update().get(pk=contact_id)
    if contact.status == ContactStatus.ARCHIVED:
        raise InvalidContactStateError("Archived contacts cannot be updated.")

    update_fields: list[str] = []
    if display_name is not None:
        contact.display_name = display_name
        update_fields.append("display_name")
    if phone is not None:
        contact.phone = phone
        update_fields.append("phone")
    if communication_identities is not None:
        contact.communication_identities = communication_identities
        update_fields.append("communication_identities")
    if preferred_channel is not None:
        contact.preferred_channel = preferred_channel
        update_fields.append("preferred_channel")
    if photo_reference is not None:
        contact.photo_reference = photo_reference
        update_fields.append("photo_reference")

    if update_fields:
        update_fields.append("updated_at")
        contact.save(update_fields=update_fields)

    emit_contact_updated(contact_id=contact.id, discriminator="fields-updated")
    return contact


@transaction.atomic
def archive_contact(*, contact_id: uuid.UUID) -> Contact:
    contact = Contact.objects.select_for_update().get(pk=contact_id)
    if contact.status == ContactStatus.ARCHIVED:
        return contact

    now = timezone.now()
    contact.status = ContactStatus.ARCHIVED
    contact.archived_at = now
    contact.is_priority = False
    contact.save(update_fields=["status", "archived_at", "is_priority", "updated_at"])
    emit_contact_archived(contact_id=contact.id)
    return contact


@transaction.atomic
def set_priority_contact(*, contact_id: uuid.UUID) -> Contact:
    contact = Contact.objects.select_for_update().get(pk=contact_id)
    if contact.status == ContactStatus.ARCHIVED:
        raise InvalidContactStateError("Archived contacts cannot be priority contacts.")
    contact.is_priority = True
    contact.save(update_fields=["is_priority", "updated_at"])
    emit_contact_updated(contact_id=contact.id, discriminator="priority-set")
    return contact


@transaction.atomic
def remove_priority_contact(*, contact_id: uuid.UUID) -> Contact:
    contact = Contact.objects.select_for_update().get(pk=contact_id)
    contact.is_priority = False
    contact.save(update_fields=["is_priority", "updated_at"])
    emit_contact_updated(contact_id=contact.id, discriminator="priority-removed")
    return contact
