"""Call join orchestration: persistent provider rooms/users plus domain sessions."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from django.conf import settings
from django.db import transaction

from domains.communication.enums import SessionStatus, TERMINAL_SESSION_STATUSES
from domains.communication.exceptions import ContactNotFoundError
from domains.communication.models import Contact
from domains.communication.providers import CommunicationProvider, ProviderLogin, ProviderRoom, ProviderUser
from domains.communication.services.sessions import (
    cancel_session,
    end_session,
    get_active_session,
    get_session,
    initiate_session,
    record_call_attempt,
)
from infrastructure.communication.factory import get_communication_provider
from infrastructure.communication.models import (
    ProviderCallBinding,
    ProviderRoomBinding,
    ProviderSubjectType,
    ProviderUserBinding,
)

DEFAULT_PROVIDER_NAME = "skyroom"


@dataclass(frozen=True, slots=True)
class CallJoinResult:
    join_token: str
    expires_at: datetime
    session_id: uuid.UUID | None = None


def _provider_name() -> str:
    name = getattr(settings, "COMMUNICATION_PROVIDER", DEFAULT_PROVIDER_NAME)
    if name == "fake":
        return "fake"
    return DEFAULT_PROVIDER_NAME


def _ttl_seconds() -> int:
    return int(getattr(settings, "COMMUNICATION_LOGIN_TTL_SECONDS", 3600))


def room_key_for_elder(elder_id: uuid.UUID) -> str:
    return f"yara-elder-{elder_id.hex}"


def user_key_for_subject(*, subject_type: str, subject_id: uuid.UUID) -> str:
    if subject_type == ProviderSubjectType.ELDER_HUB:
        return f"yara-hub-{subject_id.hex}"
    return f"yara-user-{subject_id.hex}"


def _ensure_room_binding(
    *,
    elder_id: uuid.UUID,
    title: str,
    provider: CommunicationProvider,
) -> tuple[ProviderRoomBinding, ProviderRoom]:
    provider_name = _provider_name()
    room = provider.ensure_room(room_key=room_key_for_elder(elder_id), title=title)
    binding, created = ProviderRoomBinding.objects.get_or_create(
        provider=provider_name,
        elder_id=elder_id,
        defaults={
            "room_key": room.key,
            "external_room_id": room.external_id,
        },
    )
    if not created and (
        binding.external_room_id != room.external_id or binding.room_key != room.key
    ):
        # Panel-created rooms keep the same name; refresh a stale numeric id
        # so createLoginUrl hits the live room instead of an expired leftover.
        binding.room_key = room.key
        binding.external_room_id = room.external_id
        binding.save(update_fields=["room_key", "external_room_id"])
    return binding, room


def _ensure_user_binding(
    *,
    subject_type: str,
    subject_id: uuid.UUID,
    display_name: str,
    provider: CommunicationProvider,
) -> tuple[ProviderUserBinding, ProviderUser]:
    provider_name = _provider_name()
    binding = ProviderUserBinding.objects.filter(
        provider=provider_name,
        subject_type=subject_type,
        subject_id=subject_id,
    ).first()
    if binding is not None:
        return binding, ProviderUser(
            key=binding.user_key,
            external_id=binding.external_user_id,
            display_name=display_name or binding.display_name,
        )

    user = provider.ensure_user(
        user_key=user_key_for_subject(subject_type=subject_type, subject_id=subject_id),
        display_name=display_name,
    )
    binding, created = ProviderUserBinding.objects.get_or_create(
        provider=provider_name,
        subject_type=subject_type,
        subject_id=subject_id,
        defaults={
            "user_key": user.key,
            "external_user_id": user.external_id,
            "display_name": display_name,
        },
    )
    if not created:
        user = ProviderUser(
            key=binding.user_key,
            external_id=binding.external_user_id,
            display_name=display_name or binding.display_name,
        )
    return binding, user


def _issue_login(
    *,
    room: ProviderRoom,
    user: ProviderUser,
    provider: CommunicationProvider,
) -> ProviderLogin:
    return provider.generate_login_url(room=room, user=user, ttl_seconds=_ttl_seconds())


@transaction.atomic
def start_call(
    *,
    elder_id: uuid.UUID,
    channel: str,
    recipient_contact_id: uuid.UUID,
    initiator_user_id: uuid.UUID | None,
    subject_type: str,
    subject_id: uuid.UUID,
    room_title: str,
    user_display_name: str,
    provider: CommunicationProvider | None = None,
) -> CallJoinResult:
    active_provider = provider or get_communication_provider()
    if not Contact.objects.filter(pk=recipient_contact_id, elder_id=elder_id).exists():
        raise ContactNotFoundError("Contact not found.")

    room_binding, room = _ensure_room_binding(
        elder_id=elder_id,
        title=room_title,
        provider=active_provider,
    )
    user_binding, user = _ensure_user_binding(
        subject_type=subject_type,
        subject_id=subject_id,
        display_name=user_display_name,
        provider=active_provider,
    )
    login = _issue_login(room=room, user=user, provider=active_provider)

    session = initiate_session(
        elder_id=elder_id,
        channel=channel,
        initiator_user_id=initiator_user_id,
        recipient_contact_id=recipient_contact_id,
    )
    record_call_attempt(session_id=session.id)
    ProviderCallBinding.objects.create(
        communication_session_id=session.id,
        room_binding=room_binding,
        user_binding=user_binding,
    )
    return CallJoinResult(
        join_token=login.login_url,
        expires_at=login.expires_at,
        session_id=session.id,
    )


@transaction.atomic
def end_call(*, session_id: uuid.UUID) -> None:
    session = get_session(session_id)
    if session.status == SessionStatus.CONNECTED:
        end_session(session_id=session_id)
        return
    if session.status in TERMINAL_SESSION_STATUSES:
        return
    cancel_session(session_id=session_id)


@transaction.atomic
def issue_login_url(
    *,
    elder_id: uuid.UUID,
    subject_type: str,
    subject_id: uuid.UUID,
    room_title: str,
    user_display_name: str,
    provider: CommunicationProvider | None = None,
) -> CallJoinResult:
    active_provider = provider or get_communication_provider()
    room_binding, room = _ensure_room_binding(
        elder_id=elder_id,
        title=room_title,
        provider=active_provider,
    )
    _user_binding, user = _ensure_user_binding(
        subject_type=subject_type,
        subject_id=subject_id,
        display_name=user_display_name,
        provider=active_provider,
    )
    login = _issue_login(room=room, user=user, provider=active_provider)
    active = get_active_session(elder_id=elder_id)
    return CallJoinResult(
        join_token=login.login_url,
        expires_at=login.expires_at,
        session_id=active.id if active is not None else None,
    )
