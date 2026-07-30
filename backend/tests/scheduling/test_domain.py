import uuid
from datetime import datetime, timedelta

import pytest
from django.utils import timezone
from zoneinfo import ZoneInfo

from domains.event.models import EventRecord
from domains.scheduling.constants import DEFAULT_GENERATION_HORIZON_DAYS
from domains.scheduling.enums import OccurrenceStatus, ScheduleExceptionType, ScheduleStatus
from domains.scheduling.exceptions import RescheduleCollisionError
from domains.scheduling.identity import compute_occurrence_id, normalize_instant
from domains.scheduling.models import Occurrence
from domains.scheduling.recurrence.engine import iter_recurrence_slots
from domains.scheduling.services.due import mark_occurrence_due, process_due_occurrences
from domains.scheduling.services.occurrences import (
    cancel_occurrence,
    generate_occurrences_for_schedule,
    get_next_occurrence,
    get_occurrences_between,
    skip_occurrence,
)
from domains.scheduling.services.schedules import (
    add_schedule_exception,
    cancel_schedule,
    create_schedule,
    pause_schedule,
    resume_schedule,
    update_schedule,
)
from tests.scheduling.conftest import _aware, _daily_schedule


@pytest.mark.django_db
def test_schedule_creation_emits_event_and_generates_occurrences():
    schedule = _daily_schedule()
    assert schedule.status == ScheduleStatus.ACTIVE
    assert Occurrence.objects.filter(schedule_definition=schedule).exists()
    assert EventRecord.objects.filter(event_type="ScheduleCreated", producer="scheduling").exists()
    assert EventRecord.objects.filter(event_type="OccurrenceScheduled", producer="scheduling").exists()


@pytest.mark.django_db
def test_recurrence_calculation_daily_timezone_aware():
    schedule = create_schedule(
        owner_reference="owner:1",
        recurrence_definition={"type": "daily", "time": "08:00"},
        timezone_name="Asia/Tehran",
        start_at=_aware(datetime(2026, 7, 1, 0, 0, tzinfo=ZoneInfo("UTC"))),
    )
    slots = list(
        iter_recurrence_slots(
            recurrence_definition=schedule.recurrence_definition,
            timezone_name=schedule.timezone,
            start_at=schedule.start_at,
            end_at=schedule.end_at,
            range_start=_aware(datetime(2026, 7, 1, 0, 0, tzinfo=ZoneInfo("UTC"))),
            range_end=_aware(datetime(2026, 7, 3, 0, 0, tzinfo=ZoneInfo("UTC"))),
        )
    )
    assert len(slots) >= 2
    local_times = [slot.original_time.astimezone(ZoneInfo("Asia/Tehran")).hour for slot in slots]
    assert all(hour == 8 for hour in local_times)


@pytest.mark.django_db
def test_stable_occurrence_identity():
    schedule = _daily_schedule()
    occurrence = Occurrence.objects.filter(schedule_definition=schedule).first()
    assert occurrence is not None
    expected_id = compute_occurrence_id(
        schedule_definition_id=schedule.id,
        original_time=occurrence.scheduled_for,
    )
    assert occurrence.id == expected_id


@pytest.mark.django_db
def test_schedule_definition_id_is_globally_stable():
    schedule = _daily_schedule()
    persisted = schedule.__class__.objects.get(pk=schedule.id)
    assert persisted.id == schedule.id


@pytest.mark.django_db
def test_reschedule_preserves_occurrence_identity():
    schedule = _daily_schedule()
    target = Occurrence.objects.filter(schedule_definition=schedule, status=OccurrenceStatus.SCHEDULED).first()
    original_id = target.id
    original_slot = normalize_instant(target.scheduled_for)
    replacement = target.scheduled_for + timedelta(hours=2)

    add_schedule_exception(
        schedule.id,
        original_time=target.scheduled_for,
        exception_type=ScheduleExceptionType.RESCHEDULE,
        replacement_time=replacement,
    )

    target.refresh_from_db()
    assert target.id == original_id
    assert target.id == compute_occurrence_id(
        schedule_definition_id=schedule.id,
        original_time=original_slot,
    )
    assert target.scheduled_for == replacement


@pytest.mark.django_db
def test_reschedule_collision_is_rejected():
    schedule = _daily_schedule()
    occurrences = list(
        Occurrence.objects.filter(schedule_definition=schedule, status=OccurrenceStatus.SCHEDULED).order_by(
            "scheduled_for"
        )[:2]
    )
    assert len(occurrences) == 2
    target, blocker = occurrences

    with pytest.raises(RescheduleCollisionError):
        add_schedule_exception(
            schedule.id,
            original_time=target.scheduled_for,
            exception_type=ScheduleExceptionType.RESCHEDULE,
            replacement_time=blocker.scheduled_for,
        )

    target.refresh_from_db()
    assert target.scheduled_for != blocker.scheduled_for


@pytest.mark.django_db
def test_generation_continues_beyond_default_horizon():
    schedule = _daily_schedule()
    original_end_at = schedule.end_at
    count_after_first = Occurrence.objects.filter(schedule_definition=schedule).count()

    range_start = timezone.now() + timedelta(days=DEFAULT_GENERATION_HORIZON_DAYS + 1)
    range_end = range_start + timedelta(days=30)
    generate_occurrences_for_schedule(
        schedule,
        range_start=range_start,
        range_end=range_end,
        emit_events=False,
    )

    count_after_second = Occurrence.objects.filter(schedule_definition=schedule).count()
    schedule.refresh_from_db()

    assert count_after_second > count_after_first
    assert schedule.end_at == original_end_at
    assert schedule.status == ScheduleStatus.ACTIVE


@pytest.mark.django_db
def test_due_transition_rolls_back_when_event_recording_fails():
    from unittest.mock import patch

    schedule = _daily_schedule()
    occurrence = Occurrence.objects.filter(schedule_definition=schedule, status=OccurrenceStatus.SCHEDULED).first()
    occurrence.scheduled_for = timezone.now() - timedelta(minutes=1)
    occurrence.save(update_fields=["scheduled_for"])

    with patch(
        "domains.scheduling.services.events.record_event",
        side_effect=RuntimeError("event recording failed"),
    ):
        with pytest.raises(RuntimeError):
            mark_occurrence_due(occurrence, occurred_at=timezone.now())

    occurrence.refresh_from_db()
    assert occurrence.status == OccurrenceStatus.SCHEDULED
    assert EventRecord.objects.filter(event_type="OccurrenceDue").count() == 0


@pytest.mark.django_db
def test_duplicate_generation_is_idempotent():
    schedule = _daily_schedule()
    first_count = Occurrence.objects.filter(schedule_definition=schedule).count()
    generate_occurrences_for_schedule(schedule, emit_events=False)
    second_count = Occurrence.objects.filter(schedule_definition=schedule).count()
    assert first_count == second_count


@pytest.mark.django_db
def test_paused_schedule_does_not_generate_new_occurrences():
    schedule = _daily_schedule()
    before = Occurrence.objects.filter(schedule_definition=schedule).count()
    pause_schedule(schedule.id)
    future_start = timezone.now() + timedelta(days=120)
    future_end = future_start + timedelta(days=30)
    generate_occurrences_for_schedule(schedule, range_start=future_start, range_end=future_end)
    after = Occurrence.objects.filter(schedule_definition=schedule).count()
    assert after == before


@pytest.mark.django_db
def test_cancelled_schedule_does_not_generate_new_occurrences():
    schedule = _daily_schedule()
    cancel_schedule(schedule.id)
    before = Occurrence.objects.filter(schedule_definition=schedule).count()
    generate_occurrences_for_schedule(schedule)
    after = Occurrence.objects.filter(schedule_definition=schedule).count()
    assert after == before


@pytest.mark.django_db
def test_pause_and_resume():
    schedule = _daily_schedule()
    pause_schedule(schedule.id)
    assert schedule.__class__.objects.get(pk=schedule.id).status == ScheduleStatus.PAUSED
    resume_schedule(schedule.id)
    assert schedule.__class__.objects.get(pk=schedule.id).status == ScheduleStatus.ACTIVE
    assert EventRecord.objects.filter(event_type="SchedulePaused").exists()
    assert EventRecord.objects.filter(event_type="ScheduleResumed").exists()


@pytest.mark.django_db
def test_update_schedule_does_not_rewrite_past_occurrences():
    schedule = _daily_schedule()
    past_occurrence = Occurrence.objects.filter(schedule_definition=schedule).order_by("scheduled_for").first()
    past_scheduled_for = past_occurrence.scheduled_for
    past_id = past_occurrence.id

    update_schedule(
        schedule.id,
        recurrence_definition={"type": "daily", "time": "09:00"},
    )

    past_occurrence.refresh_from_db()
    assert past_occurrence.id == past_id
    assert past_occurrence.scheduled_for == past_scheduled_for


@pytest.mark.django_db
def test_skip_occurrence():
    schedule = _daily_schedule()
    occurrence = Occurrence.objects.filter(schedule_definition=schedule, status=OccurrenceStatus.SCHEDULED).first()
    skipped = skip_occurrence(occurrence_id=occurrence.id)
    assert skipped.status == OccurrenceStatus.SKIPPED
    assert EventRecord.objects.filter(event_type="OccurrenceSkipped").exists()


@pytest.mark.django_db
def test_cancel_occurrence():
    schedule = _daily_schedule()
    occurrence = Occurrence.objects.filter(schedule_definition=schedule, status=OccurrenceStatus.SCHEDULED).first()
    cancelled = cancel_occurrence(occurrence_id=occurrence.id)
    assert cancelled.status == OccurrenceStatus.CANCELLED
    assert EventRecord.objects.filter(event_type="OccurrenceCancelled").exists()


@pytest.mark.django_db
def test_skipped_occurrence_cannot_become_due():
    schedule = _daily_schedule()
    occurrence = Occurrence.objects.filter(schedule_definition=schedule, status=OccurrenceStatus.SCHEDULED).first()
    skip_occurrence(occurrence_id=occurrence.id)
    occurrence.scheduled_for = timezone.now() - timedelta(minutes=5)
    occurrence.save(update_fields=["scheduled_for"])
    process_due_occurrences(now=timezone.now())
    occurrence.refresh_from_db()
    assert occurrence.status == OccurrenceStatus.SKIPPED


@pytest.mark.django_db
def test_cancelled_occurrence_cannot_become_due():
    schedule = _daily_schedule()
    occurrence = Occurrence.objects.filter(schedule_definition=schedule, status=OccurrenceStatus.SCHEDULED).first()
    cancel_occurrence(occurrence_id=occurrence.id)
    occurrence.scheduled_for = timezone.now() - timedelta(minutes=5)
    occurrence.save(update_fields=["scheduled_for"])
    process_due_occurrences(now=timezone.now())
    occurrence.refresh_from_db()
    assert occurrence.status == OccurrenceStatus.CANCELLED


@pytest.mark.django_db
def test_due_transition_and_event():
    schedule = _daily_schedule()
    occurrence = Occurrence.objects.filter(schedule_definition=schedule, status=OccurrenceStatus.SCHEDULED).first()
    occurrence.scheduled_for = timezone.now() - timedelta(minutes=1)
    occurrence.save(update_fields=["scheduled_for"])

    processed = process_due_occurrences(now=timezone.now())
    assert processed == 1
    occurrence.refresh_from_db()
    assert occurrence.status == OccurrenceStatus.DUE
    assert EventRecord.objects.filter(event_type="OccurrenceDue").count() == 1


@pytest.mark.django_db
def test_repeated_due_processing_is_idempotent():
    schedule = _daily_schedule()
    occurrence = Occurrence.objects.filter(schedule_definition=schedule, status=OccurrenceStatus.SCHEDULED).first()
    occurrence.scheduled_for = timezone.now() - timedelta(minutes=1)
    occurrence.save(update_fields=["scheduled_for"])

    first = process_due_occurrences(now=timezone.now())
    second = process_due_occurrences(now=timezone.now())
    assert first == 1
    assert second == 0
    assert EventRecord.objects.filter(event_type="OccurrenceDue").count() == 1


@pytest.mark.django_db
def test_occurrence_due_payload_identifies_occurrence():
    schedule = _daily_schedule()
    occurrence = Occurrence.objects.filter(schedule_definition=schedule, status=OccurrenceStatus.SCHEDULED).first()
    occurrence.scheduled_for = timezone.now() - timedelta(minutes=1)
    occurrence.save(update_fields=["scheduled_for"])
    process_due_occurrences(now=timezone.now())

    event = EventRecord.objects.get(event_type="OccurrenceDue")
    assert event.payload["occurrence_id"] == str(occurrence.id)
    assert event.payload["schedule_definition_id"] == str(schedule.id)


@pytest.mark.django_db
def test_schedule_exception_skip():
    schedule = _daily_schedule()
    target = Occurrence.objects.filter(schedule_definition=schedule, status=OccurrenceStatus.SCHEDULED).first()
    add_schedule_exception(
        schedule.id,
        original_time=target.scheduled_for,
        exception_type=ScheduleExceptionType.SKIP,
        reason="holiday",
    )
    target.refresh_from_db()
    assert target.status == OccurrenceStatus.SKIPPED


@pytest.mark.django_db
def test_schedule_exception_reschedule():
    schedule = _daily_schedule()
    target = Occurrence.objects.filter(schedule_definition=schedule, status=OccurrenceStatus.SCHEDULED).first()
    original_id = target.id
    replacement = target.scheduled_for + timedelta(hours=2)
    add_schedule_exception(
        schedule.id,
        original_time=target.scheduled_for,
        exception_type=ScheduleExceptionType.RESCHEDULE,
        replacement_time=replacement,
    )
    target.refresh_from_db()
    assert target.id == original_id
    assert target.scheduled_for == replacement


@pytest.mark.django_db
def test_workflow_domain_is_registered():
    from django.apps import apps

    assert apps.is_installed("domains.workflow")


@pytest.mark.django_db
def test_owner_reference_is_opaque():
    schedule = create_schedule(
        owner_reference="care_activity:opaque-ref",
        recurrence_definition={"type": "once"},
        timezone_name="UTC",
        start_at=timezone.now() + timedelta(days=1),
    )
    assert schedule.owner_reference == "care_activity:opaque-ref"


@pytest.mark.django_db
def test_get_occurrences_between():
    schedule = _daily_schedule()
    start = timezone.now()
    end = timezone.now() + timedelta(days=30)
    results = get_occurrences_between(schedule_definition_id=schedule.id, start=start, end=end)
    assert results
    assert all(start <= item.scheduled_for <= end for item in results)


@pytest.mark.django_db
def test_get_next_occurrence():
    schedule = _daily_schedule()
    nxt = get_next_occurrence(schedule_definition_id=schedule.id, after=timezone.now())
    assert nxt is not None
    assert nxt.status == OccurrenceStatus.SCHEDULED
