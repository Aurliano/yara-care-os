"""Care event publication via the Event domain."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from django.utils import timezone

from domains.care.identity import compute_care_event_id
from domains.event.services.recording import EventInput, publish_event, record_event

EVENT_VERSION = 1
PRODUCER = "care"


def publish_care_fact(
    *,
    event_type: str,
    subject_id: uuid.UUID,
    occurred_at: datetime,
    payload: dict[str, Any],
    discriminator: str = "",
) -> None:
    event_id = compute_care_event_id(
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


def emit_care_activity_created(*, care_activity_id: uuid.UUID, elder_id: uuid.UUID, activity_type: str) -> None:
    publish_care_fact(
        event_type="CareActivityCreated",
        subject_id=care_activity_id,
        occurred_at=timezone.now(),
        payload={
            "care_activity_id": str(care_activity_id),
            "elder_id": str(elder_id),
            "activity_type": activity_type,
        },
    )


def emit_care_activity_updated(*, care_activity_id: uuid.UUID, status: str) -> None:
    publish_care_fact(
        event_type="CareActivityUpdated",
        subject_id=care_activity_id,
        occurred_at=timezone.now(),
        payload={
            "care_activity_id": str(care_activity_id),
            "status": status,
        },
    )


def emit_care_activity_paused(*, care_activity_id: uuid.UUID) -> None:
    publish_care_fact(
        event_type="CareActivityPaused",
        subject_id=care_activity_id,
        occurred_at=timezone.now(),
        payload={"care_activity_id": str(care_activity_id)},
    )


def emit_care_activity_resumed(*, care_activity_id: uuid.UUID) -> None:
    publish_care_fact(
        event_type="CareActivityResumed",
        subject_id=care_activity_id,
        occurred_at=timezone.now(),
        payload={"care_activity_id": str(care_activity_id)},
    )


def emit_care_activity_ended(*, care_activity_id: uuid.UUID) -> None:
    publish_care_fact(
        event_type="CareActivityEnded",
        subject_id=care_activity_id,
        occurred_at=timezone.now(),
        payload={"care_activity_id": str(care_activity_id)},
    )


def emit_prescription_created(*, prescription_id: uuid.UUID, care_activity_id: uuid.UUID) -> None:
    publish_care_fact(
        event_type="PrescriptionCreated",
        subject_id=prescription_id,
        occurred_at=timezone.now(),
        payload={
            "prescription_id": str(prescription_id),
            "care_activity_id": str(care_activity_id),
        },
    )


def emit_prescription_updated(*, prescription_id: uuid.UUID) -> None:
    publish_care_fact(
        event_type="PrescriptionUpdated",
        subject_id=prescription_id,
        occurred_at=timezone.now(),
        payload={"prescription_id": str(prescription_id)},
    )


def emit_care_activity_completed(
    *,
    care_activity_id: uuid.UUID,
    care_completion_id: uuid.UUID,
    workflow_execution_id: uuid.UUID,
) -> None:
    publish_care_fact(
        event_type="CareActivityCompleted",
        subject_id=care_completion_id,
        occurred_at=timezone.now(),
        payload={
            "care_activity_id": str(care_activity_id),
            "care_completion_id": str(care_completion_id),
            "workflow_execution_id": str(workflow_execution_id),
        },
    )


def emit_medication_taken(
    *,
    care_activity_id: uuid.UUID,
    care_completion_id: uuid.UUID,
    workflow_execution_id: uuid.UUID,
) -> None:
    from domains.care.services.activities import get_care_activity

    activity = get_care_activity(care_activity_id)
    publish_care_fact(
        event_type="MedicationTaken",
        subject_id=care_completion_id,
        occurred_at=timezone.now(),
        payload={
            "care_activity_id": str(care_activity_id),
            "care_completion_id": str(care_completion_id),
            "workflow_execution_id": str(workflow_execution_id),
            "elder_id": str(activity.elder_id),
            "aggregate_version": activity.aggregate_version,
        },
    )


def emit_medication_missed(
    *,
    care_activity_id: uuid.UUID,
    care_completion_id: uuid.UUID,
    workflow_execution_id: uuid.UUID,
) -> None:
    from domains.care.services.activities import get_care_activity

    activity = get_care_activity(care_activity_id)
    publish_care_fact(
        event_type="MedicationMissed",
        subject_id=care_completion_id,
        occurred_at=timezone.now(),
        payload={
            "care_activity_id": str(care_activity_id),
            "care_completion_id": str(care_completion_id),
            "workflow_execution_id": str(workflow_execution_id),
            "elder_id": str(activity.elder_id),
            "aggregate_version": activity.aggregate_version,
        },
    )
