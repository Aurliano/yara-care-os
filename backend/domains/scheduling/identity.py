"""Deterministic occurrence identity helpers.

Stable identity invariants:

- ``ScheduleDefinition.id`` is a globally stable UUID primary key assigned at
  creation time. It is suitable for Backend/Hub synchronization reconciliation.
- ``Occurrence.id`` is deterministically derived from ``schedule_definition_id``
  and the canonical original logical recurrence slot (UTC-normalized instant).
- ``RESCHEDULE`` may change ``scheduled_for`` only; it must never change
  ``Occurrence.id``.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from django.utils import timezone as django_timezone
from zoneinfo import ZoneInfo

from domains.scheduling.constants import SCHEDULING_NAMESPACE


def normalize_instant(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("Datetime must be timezone-aware.")
    return value.astimezone(ZoneInfo("UTC")).replace(microsecond=0)


def compute_occurrence_id(*, schedule_definition_id: uuid.UUID, original_time: datetime) -> uuid.UUID:
    """Stable identity for one logical occurrence slot."""
    instant = normalize_instant(original_time)
    key = f"{schedule_definition_id}:{instant.isoformat()}"
    return uuid.uuid5(SCHEDULING_NAMESPACE, key)


def compute_scheduling_event_id(*, event_type: str, subject_id: uuid.UUID) -> uuid.UUID:
    """Stable event identity for one Scheduling fact."""
    key = f"{event_type}:{subject_id}"
    return uuid.uuid5(SCHEDULING_NAMESPACE, key)


def utc_now() -> datetime:
    return django_timezone.now().astimezone(ZoneInfo("UTC")).replace(microsecond=0)
