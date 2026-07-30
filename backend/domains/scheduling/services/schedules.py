"""Schedule definition commands and queries."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from django.db import transaction
from django.utils import timezone

from domains.scheduling.enums import OccurrenceStatus, ScheduleExceptionType, ScheduleStatus
from domains.scheduling.exceptions import InvalidScheduleStateError, RescheduleCollisionError, ScheduleNotFoundError
from domains.scheduling.models import Occurrence, ScheduleDefinition, ScheduleException
from domains.scheduling.recurrence.engine import validate_recurrence_definition
from domains.scheduling.services.events import (
    emit_schedule_cancelled,
    emit_schedule_created,
    emit_schedule_paused,
    emit_schedule_resumed,
    emit_schedule_updated,
)
from domains.scheduling.services.occurrences import (
    assert_reschedule_does_not_collide,
    ensure_schedule_exists,
    generate_occurrences_for_schedule,
)
from domains.scheduling.identity import compute_occurrence_id


def get_schedule(schedule_definition_id: uuid.UUID) -> ScheduleDefinition:
    return ensure_schedule_exists(schedule_definition_id)


@transaction.atomic
def create_schedule(
    *,
    owner_reference: str,
    recurrence_definition: dict[str, Any],
    timezone_name: str,
    start_at: datetime,
    end_at: datetime | None = None,
) -> ScheduleDefinition:
    validate_recurrence_definition(recurrence_definition)
    schedule = ScheduleDefinition.objects.create(
        owner_reference=owner_reference,
        recurrence_definition=recurrence_definition,
        timezone=timezone_name,
        start_at=start_at,
        end_at=end_at,
        status=ScheduleStatus.ACTIVE,
    )
    emit_schedule_created(
        schedule_id=schedule.id,
        owner_reference=schedule.owner_reference,
        timezone_name=schedule.timezone,
        status=schedule.status,
    )
    generate_occurrences_for_schedule(schedule)
    return schedule


@transaction.atomic
def update_schedule(
    schedule_definition_id: uuid.UUID,
    *,
    recurrence_definition: dict[str, Any] | None = None,
    timezone_name: str | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> ScheduleDefinition:
    schedule = get_schedule(schedule_definition_id)
    if schedule.status in {ScheduleStatus.CANCELLED, ScheduleStatus.ENDED}:
        raise InvalidScheduleStateError("Cannot update a cancelled or ended schedule.")

    if recurrence_definition is not None:
        validate_recurrence_definition(recurrence_definition)
        schedule.recurrence_definition = recurrence_definition
    if timezone_name is not None:
        schedule.timezone = timezone_name
    if start_at is not None:
        schedule.start_at = start_at
    if end_at is not None:
        schedule.end_at = end_at

    schedule.save()
    emit_schedule_updated(schedule_id=schedule.id, status=schedule.status)

    if schedule.status == ScheduleStatus.ACTIVE:
        generate_occurrences_for_schedule(schedule, range_start=timezone.now())
    return schedule


@transaction.atomic
def pause_schedule(schedule_definition_id: uuid.UUID) -> ScheduleDefinition:
    schedule = get_schedule(schedule_definition_id)
    if schedule.status != ScheduleStatus.ACTIVE:
        raise InvalidScheduleStateError("Only active schedules can be paused.")
    schedule.status = ScheduleStatus.PAUSED
    schedule.save(update_fields=["status", "updated_at"])
    emit_schedule_paused(schedule_id=schedule.id)
    return schedule


@transaction.atomic
def resume_schedule(schedule_definition_id: uuid.UUID) -> ScheduleDefinition:
    schedule = get_schedule(schedule_definition_id)
    if schedule.status != ScheduleStatus.PAUSED:
        raise InvalidScheduleStateError("Only paused schedules can be resumed.")
    schedule.status = ScheduleStatus.ACTIVE
    schedule.save(update_fields=["status", "updated_at"])
    emit_schedule_resumed(schedule_id=schedule.id)
    generate_occurrences_for_schedule(schedule, range_start=timezone.now())
    return schedule


@transaction.atomic
def cancel_schedule(schedule_definition_id: uuid.UUID) -> ScheduleDefinition:
    schedule = get_schedule(schedule_definition_id)
    if schedule.status == ScheduleStatus.CANCELLED:
        return schedule
    if schedule.status == ScheduleStatus.ENDED:
        raise InvalidScheduleStateError("Ended schedules cannot be cancelled.")
    schedule.status = ScheduleStatus.CANCELLED
    schedule.save(update_fields=["status", "updated_at"])
    emit_schedule_cancelled(schedule_id=schedule.id)
    return schedule


@transaction.atomic
def add_schedule_exception(
    schedule_definition_id: uuid.UUID,
    *,
    original_time: datetime,
    exception_type: str,
    replacement_time: datetime | None = None,
    reason: str = "",
) -> ScheduleException:
    schedule = get_schedule(schedule_definition_id)
    if schedule.status not in {ScheduleStatus.ACTIVE, ScheduleStatus.PAUSED}:
        raise InvalidScheduleStateError("Exceptions can only be added to active or paused schedules.")
    if exception_type == ScheduleExceptionType.RESCHEDULE and replacement_time is None:
        raise InvalidScheduleStateError("Reschedule exceptions require replacement_time.")

    occurrence_id = compute_occurrence_id(
        schedule_definition_id=schedule.id,
        original_time=original_time,
    )
    if exception_type == ScheduleExceptionType.RESCHEDULE:
        assert_reschedule_does_not_collide(
            schedule_definition_id=schedule.id,
            replacement_time=replacement_time,
            occurrence_id=occurrence_id,
        )

    exception, _ = ScheduleException.objects.update_or_create(
        schedule_definition=schedule,
        original_time=original_time,
        defaults={
            "exception_type": exception_type,
            "replacement_time": replacement_time,
            "reason": reason,
        },
    )

    _apply_exception_to_existing_occurrence(schedule=schedule, exception=exception)

    if schedule.status == ScheduleStatus.ACTIVE:
        generate_occurrences_for_schedule(schedule, range_start=timezone.now())
    return exception


def _apply_exception_to_existing_occurrence(
    *,
    schedule: ScheduleDefinition,
    exception: ScheduleException,
) -> None:
    occurrence_id = compute_occurrence_id(
        schedule_definition_id=schedule.id,
        original_time=exception.original_time,
    )
    occurrence = Occurrence.objects.filter(pk=occurrence_id).first()
    if occurrence is None:
        return

    if occurrence.status != OccurrenceStatus.SCHEDULED:
        return

    if exception.exception_type == ScheduleExceptionType.SKIP:
        occurrence.status = OccurrenceStatus.SKIPPED
    elif exception.exception_type == ScheduleExceptionType.CANCEL:
        occurrence.status = OccurrenceStatus.CANCELLED
    elif exception.exception_type == ScheduleExceptionType.RESCHEDULE and exception.replacement_time is not None:
        assert_reschedule_does_not_collide(
            schedule_definition_id=schedule.id,
            replacement_time=exception.replacement_time,
            occurrence_id=occurrence.id,
        )
        occurrence.scheduled_for = exception.replacement_time

    occurrence.save(update_fields=["scheduled_for", "status"])
