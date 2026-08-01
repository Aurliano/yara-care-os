"""Communication event publication via the Event domain."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from django.utils import timezone

from domains.communication.identity import compute_communication_event_id
from domains.event.services.recording import EventInput, publish_event, record_event

EVENT_VERSION = 1
PRODUCER = "communication"


def publish_communication_fact(
    *,
    event_type: str,
    subject_id: uuid.UUID,
    occurred_at: datetime,
    payload: dict[str, Any],
    discriminator: str = "",
) -> None:
    event_id = compute_communication_event_id(
        event_type=event_type,
        subject_id=subject_id,
        discriminator=discriminator,
    )
    event = record_event(
        EventInput(
            event_id=event_id,
            event_type=event_type,
            event_version=EVENT_VERSION,
            producer=PRODUCER,
            occurred_at=occurred_at,
            payload=payload,
        )
    )
    publish_event(event_id=event.id)


def emit_contact_created(*, contact_id: uuid.UUID, elder_id: uuid.UUID) -> None:
    publish_communication_fact(
        event_type="ContactCreated",
        subject_id=contact_id,
        occurred_at=timezone.now(),
        payload={"contact_id": str(contact_id), "elder_id": str(elder_id)},
    )


def emit_contact_updated(*, contact_id: uuid.UUID, discriminator: str = "") -> None:
    publish_communication_fact(
        event_type="ContactUpdated",
        subject_id=contact_id,
        occurred_at=timezone.now(),
        discriminator=discriminator,
        payload={"contact_id": str(contact_id)},
    )


def emit_contact_archived(*, contact_id: uuid.UUID) -> None:
    publish_communication_fact(
        event_type="ContactArchived",
        subject_id=contact_id,
        occurred_at=timezone.now(),
        payload={"contact_id": str(contact_id)},
    )


def emit_session_initiated(*, session_id: uuid.UUID, elder_id: uuid.UUID, channel: str) -> None:
    publish_communication_fact(
        event_type="CommunicationSessionInitiated",
        subject_id=session_id,
        occurred_at=timezone.now(),
        payload={
            "communication_session_id": str(session_id),
            "elder_id": str(elder_id),
            "channel": channel,
        },
    )


def emit_session_connected(*, session_id: uuid.UUID) -> None:
    publish_communication_fact(
        event_type="CommunicationSessionConnected",
        subject_id=session_id,
        occurred_at=timezone.now(),
        payload={"communication_session_id": str(session_id)},
    )


def emit_session_ended(
    *,
    session_id: uuid.UUID,
    outcome: str,
    elder_id: uuid.UUID | None = None,
    external_execution_reference: uuid.UUID | None = None,
) -> None:
    publish_communication_fact(
        event_type="CommunicationSessionEnded",
        subject_id=session_id,
        occurred_at=timezone.now(),
        discriminator=outcome,
        payload={
            "communication_session_id": str(session_id),
            "outcome": outcome,
            "elder_id": str(elder_id) if elder_id else None,
            "external_execution_reference": (
                str(external_execution_reference) if external_execution_reference else None
            ),
        },
    )


def emit_session_missed(*, session_id: uuid.UUID) -> None:
    publish_communication_fact(
        event_type="CommunicationSessionMissed",
        subject_id=session_id,
        occurred_at=timezone.now(),
        payload={"communication_session_id": str(session_id)},
    )


def emit_session_declined(*, session_id: uuid.UUID) -> None:
    publish_communication_fact(
        event_type="CommunicationSessionDeclined",
        subject_id=session_id,
        occurred_at=timezone.now(),
        payload={"communication_session_id": str(session_id)},
    )


def emit_session_failed(*, session_id: uuid.UUID, reason: str = "") -> None:
    publish_communication_fact(
        event_type="CommunicationSessionFailed",
        subject_id=session_id,
        occurred_at=timezone.now(),
        payload={
            "communication_session_id": str(session_id),
            "reason": reason,
        },
    )


def emit_call_attempt_started(*, attempt_id: uuid.UUID, session_id: uuid.UUID, attempt_number: int) -> None:
    publish_communication_fact(
        event_type="CallAttemptStarted",
        subject_id=attempt_id,
        occurred_at=timezone.now(),
        discriminator=str(attempt_number),
        payload={
            "call_attempt_id": str(attempt_id),
            "communication_session_id": str(session_id),
            "attempt_number": attempt_number,
        },
    )


def emit_call_attempt_failed(*, attempt_id: uuid.UUID, session_id: uuid.UUID, reason: str = "") -> None:
    publish_communication_fact(
        event_type="CallAttemptFailed",
        subject_id=attempt_id,
        occurred_at=timezone.now(),
        payload={
            "call_attempt_id": str(attempt_id),
            "communication_session_id": str(session_id),
            "reason": reason,
        },
    )
