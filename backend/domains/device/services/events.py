"""Device event publication via the Event domain."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from django.utils import timezone

from domains.device.identity import compute_device_event_id
from domains.event.services.recording import EventInput, publish_event, record_event

EVENT_VERSION = 1
PRODUCER = "device"


def publish_device_fact(
    *,
    event_type: str,
    subject_id: uuid.UUID,
    occurred_at: datetime,
    payload: dict[str, Any],
    discriminator: str = "",
) -> None:
    event_id = compute_device_event_id(
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


def emit_device_online(*, device_id: uuid.UUID) -> None:
    publish_device_fact(
        event_type="DeviceOnline",
        subject_id=device_id,
        occurred_at=timezone.now(),
        payload={"device_id": str(device_id)},
    )


def emit_device_offline(*, device_id: uuid.UUID) -> None:
    publish_device_fact(
        event_type="DeviceOffline",
        subject_id=device_id,
        occurred_at=timezone.now(),
        payload={"device_id": str(device_id)},
    )


def emit_device_paired(*, pairing_id: uuid.UUID, hub_device_id: uuid.UUID, peripheral_device_id: uuid.UUID) -> None:
    publish_device_fact(
        event_type="DevicePaired",
        subject_id=pairing_id,
        occurred_at=timezone.now(),
        payload={
            "pairing_id": str(pairing_id),
            "hub_device_id": str(hub_device_id),
            "peripheral_device_id": str(peripheral_device_id),
        },
    )


def emit_compartment_opened(*, compartment_id: uuid.UUID, device_id: uuid.UUID) -> None:
    publish_device_fact(
        event_type="CompartmentOpened",
        subject_id=compartment_id,
        occurred_at=timezone.now(),
        payload={
            "compartment_id": str(compartment_id),
            "device_id": str(device_id),
        },
    )


def emit_compartment_closed(*, compartment_id: uuid.UUID, device_id: uuid.UUID) -> None:
    publish_device_fact(
        event_type="CompartmentClosed",
        subject_id=compartment_id,
        occurred_at=timezone.now(),
        payload={
            "compartment_id": str(compartment_id),
            "device_id": str(device_id),
        },
    )


def emit_device_command_completed(*, command_id: uuid.UUID, device_id: uuid.UUID) -> None:
    publish_device_fact(
        event_type="DeviceCommandCompleted",
        subject_id=command_id,
        occurred_at=timezone.now(),
        payload={
            "command_id": str(command_id),
            "device_id": str(device_id),
        },
    )


def emit_device_command_failed(*, command_id: uuid.UUID, device_id: uuid.UUID, reason: str = "") -> None:
    publish_device_fact(
        event_type="DeviceCommandFailed",
        subject_id=command_id,
        occurred_at=timezone.now(),
        payload={
            "command_id": str(command_id),
            "device_id": str(device_id),
            "failure_reason": reason,
        },
    )
