import threading
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.utils import timezone
from rest_framework import status

from domains.care.enums import CareActivityStatus
from domains.care.models import CareActivity, Prescription
from domains.care.services.activities import create_care_activity, end_care_activity
from domains.care.services.prescriptions import create_prescription
from domains.event.models import EventOutbox, EventRecord
from domains.scheduling.enums import OccurrenceStatus, ScheduleExceptionType, ScheduleStatus
from domains.scheduling.exceptions import InvalidRecurrenceDefinitionError
from domains.scheduling.models import Occurrence, ScheduleDefinition
from domains.scheduling.recurrence.engine import (
    extract_and_validate_times,
    iter_recurrence_slots,
    validate_recurrence_definition,
)
from domains.scheduling.services.occurrences import (
    cancel_occurrence,
    generate_occurrences_for_schedule,
    skip_occurrence,
)
from domains.scheduling.services.schedules import (
    add_schedule_exception,
    create_schedule,
)
from domains.workflow.services.executions import create_workflow_definition
from integration.context import IntegrationContext
from integration.handlers.events import (
    handle_occurrence_cancelled,
    handle_occurrence_skipped,
    handle_schedule_exception_added,
)
from tests.care.conftest import _aware, _base_workflow_definition


def _make_wf():
    return create_workflow_definition(
        code=f"wf-c2-{uuid.uuid4().hex[:8]}",
        name="C2 Workflow",
        definition=_base_workflow_definition(),
    )


# ==============================================================================
# 1. CANONICAL times[] VALIDATION & NORMALIZATION TESTS
# ==============================================================================


def test_times_validation_valid_formats_and_sorting():
    definition = {"type": "daily", "times": ["14:30", "08:00", " 20:15 "]}
    sorted_times = extract_and_validate_times(definition)
    assert sorted_times == ["08:00", "14:30", "20:15"]


def test_times_validation_rejects_duplicate_times():
    definition = {"type": "daily", "times": ["08:00", "12:00", "08:00"]}
    with pytest.raises(InvalidRecurrenceDefinitionError, match="Duplicate times"):
        extract_and_validate_times(definition)


def test_times_validation_rejects_empty_times_for_recurring():
    definition = {"type": "daily", "times": []}
    with pytest.raises(InvalidRecurrenceDefinitionError, match="cannot be empty"):
        extract_and_validate_times(definition, required=True)


def test_times_validation_rejects_invalid_time_strings():
    invalid_cases = ["24:00", "08:60", "8:00", "8:3", "morning", "12:00:00", "25:10"]
    for bad in invalid_cases:
        with pytest.raises(InvalidRecurrenceDefinitionError):
            extract_and_validate_times({"type": "daily", "times": [bad]})


def test_times_backward_compatibility_with_scalar_time():
    definition = {"type": "daily", "time": " 08:30 "}
    assert extract_and_validate_times(definition) == ["08:30"]


def test_rejection_of_hourly_recurrence():
    with pytest.raises(InvalidRecurrenceDefinitionError, match="Hourly interval"):
        validate_recurrence_definition({"type": "every_n_hours", "every": 8})
    with pytest.raises(InvalidRecurrenceDefinitionError, match="Hourly interval"):
        validate_recurrence_definition({"type": "interval", "unit": "hours", "every": 6})


def test_once_recurrence_rejects_multiple_times():
    # C1.5 MDS-02: once represents a single occurrence
    with pytest.raises(InvalidRecurrenceDefinitionError, match="does not support multiple time slots"):
        validate_recurrence_definition({"type": "once", "times": ["08:00", "14:00"]})

    # Single time is valid
    validate_recurrence_definition({"type": "once", "times": ["08:00"]})
    validate_recurrence_definition({"type": "once", "time": "08:00"})
    validate_recurrence_definition({"type": "once"})


# ==============================================================================
# 2. OCCURRENCE GENERATION FOR MULTI-DOSE FREQUENCIES
# ==============================================================================


@pytest.mark.django_db
def test_daily_multi_dose_occurrence_generation():
    start_at = _aware(datetime(2026, 10, 1, 0, 0, tzinfo=ZoneInfo("UTC")))
    schedule = create_schedule(
        owner_reference="prescription:test-1",
        recurrence_definition={"type": "daily", "times": ["08:00", "14:00", "20:00"]},
        timezone_name="Asia/Tehran",
        start_at=start_at,
    )

    occurrences = Occurrence.objects.filter(schedule_definition=schedule).order_by("scheduled_for")
    assert occurrences.count() >= 3

    occ_list = list(occurrences[:6])
    times_seen = set()
    for occ in occ_list:
        assert occ.schedule_definition_id == schedule.id
        times_seen.add(occ.scheduled_for)
    assert len(times_seen) == len(occ_list)

    tehran_hours = [occ.scheduled_for.astimezone(ZoneInfo("Asia/Tehran")).hour for occ in occ_list[:3]]
    assert sorted(tehran_hours) == [8, 14, 20]



@pytest.mark.django_db
def test_specific_days_multi_dose_occurrence_generation():
    start_at = _aware(datetime(2026, 10, 1, 0, 0, tzinfo=ZoneInfo("UTC")))
    schedule = create_schedule(
        owner_reference="prescription:test-specific",
        recurrence_definition={
            "type": "specific_days",
            "days": ["SAT", "TUE"],
            "times": ["09:00", "18:00"],
        },
        timezone_name="Asia/Tehran",
        start_at=start_at,
    )
    occurrences = list(Occurrence.objects.filter(schedule_definition=schedule).order_by("scheduled_for")[:6])
    assert len(occurrences) >= 4
    for occ in occurrences:
        local_dt = occ.scheduled_for.astimezone(ZoneInfo("Asia/Tehran"))
        weekday_code = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"][local_dt.weekday()]
        assert weekday_code in ["SAT", "TUE"]
        assert (local_dt.hour, local_dt.minute) in [(9, 0), (18, 0)]


@pytest.mark.django_db
def test_every_n_days_occurrence_generation():
    start_at = _aware(datetime(2026, 10, 1, 0, 0, tzinfo=ZoneInfo("UTC")))
    schedule = create_schedule(
        owner_reference="prescription:test-every-n",
        recurrence_definition={
            "type": "every_n_days",
            "every": 2,
            "times": ["08:00", "20:00"],
        },
        timezone_name="Asia/Tehran",
        start_at=start_at,
    )
    occurrences = list(Occurrence.objects.filter(schedule_definition=schedule).order_by("scheduled_for")[:4])
    assert len(occurrences) == 4
    dates = [occ.scheduled_for.astimezone(ZoneInfo("Asia/Tehran")).date() for occ in occurrences]
    assert dates[0] == dates[1]
    assert dates[2] == dates[3]
    assert (dates[2] - dates[0]).days == 2


# ==============================================================================
# 3. IDEMPOTENT PLAN CREATION (MDS-04 & DM-18)
# ==============================================================================


@pytest.mark.django_db
def test_idempotent_prescription_creation_prevents_duplicate_aggregate(
    authenticated_client, elder, db
):
    wf = _make_wf()
    url = f"/api/v1/elders/{elder.id}/prescriptions/"
    idempotency_key = str(uuid.uuid4())

    payload = {
        "workflow_definition_id": str(wf.id),
        "recurrence_definition": {"type": "daily", "times": ["08:00", "20:00"]},
        "timezone_name": "Asia/Tehran",
        "start_at": "2026-10-01T00:00:00Z",
        "display_title": "Aspirin 81mg",
        "medication_reference": "Aspirin 81mg",
        "dosage_information": "1 tablet",
        "elder_friendly_description": "Heart medication",
    }

    # First attempt
    res1 = authenticated_client.post(
        url,
        payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY=idempotency_key,
    )
    assert res1.status_code == status.HTTP_201_CREATED
    created_id = res1.data["care_activity_id"]

    # Second attempt with exact same key (simulating retry / double-tap)
    res2 = authenticated_client.post(
        url,
        payload,
        format="json",
        HTTP_IDEMPOTENCY_KEY=idempotency_key,
    )
    assert res2.status_code == status.HTTP_201_CREATED
    assert res2.data["care_activity_id"] == created_id

    # Verify only ONE CareActivity and ONE Prescription were created
    assert CareActivity.objects.filter(elder_id=elder.id, display_title="Aspirin 81mg").count() == 1
    assert Prescription.objects.filter(care_activity_id=created_id).count() == 1


@pytest.mark.django_db
def test_different_idempotency_keys_create_independent_plans(
    authenticated_client, elder, db
):
    wf = _make_wf()
    url = f"/api/v1/elders/{elder.id}/prescriptions/"

    payload = {
        "workflow_definition_id": str(wf.id),
        "recurrence_definition": {"type": "daily", "times": ["08:00"]},
        "timezone_name": "Asia/Tehran",
        "start_at": "2026-10-01T00:00:00Z",
        "display_title": "Metformin",
        "medication_reference": "Metformin",
        "dosage_information": "500mg",
        "elder_friendly_description": "Diabetes medication",
    }

    res1 = authenticated_client.post(url, payload, format="json", HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
    res2 = authenticated_client.post(url, payload, format="json", HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))

    assert res1.status_code == status.HTTP_201_CREATED
    assert res2.status_code == status.HTTP_201_CREATED
    assert res1.data["care_activity_id"] != res2.data["care_activity_id"]
    assert CareActivity.objects.filter(elder_id=elder.id, display_title="Metformin").count() == 2


@pytest.mark.django_db(transaction=True)
def test_concurrent_idempotent_requests_create_only_one_aggregate(
    authenticated_client, elder
):
    """P0 Concurrency test: simultaneous requests with same key must not create duplicate aggregates."""
    wf = _make_wf()
    url = f"/api/v1/elders/{elder.id}/prescriptions/"
    shared_key = str(uuid.uuid4())

    payload = {
        "workflow_definition_id": str(wf.id),
        "recurrence_definition": {"type": "daily", "times": ["09:00"]},
        "timezone_name": "Asia/Tehran",
        "start_at": "2026-10-01T00:00:00Z",
        "display_title": "Concurrent Drug",
        "medication_reference": "Concurrent Drug",
        "dosage_information": "10mg",
        "elder_friendly_description": "Take with breakfast",
    }

    results = []
    errors = []

    def make_request():
        try:
            res = authenticated_client.post(
                url,
                payload,
                format="json",
                HTTP_IDEMPOTENCY_KEY=shared_key,
            )
            results.append(res)
        except Exception as e:
            errors.append(e)

    # Launch 2 threads concurrently with same idempotency key
    t1 = threading.Thread(target=make_request)
    t2 = threading.Thread(target=make_request)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert len(errors) == 0
    assert len(results) == 2

    # Both requests must succeed with HTTP 201
    assert results[0].status_code == status.HTTP_201_CREATED
    assert results[1].status_code == status.HTTP_201_CREATED

    # Both must reference the exact same aggregate ID
    id1 = results[0].data["care_activity_id"]
    id2 = results[1].data["care_activity_id"]
    assert id1 == id2

    # Only ONE aggregate exists in the database
    assert CareActivity.objects.filter(elder_id=elder.id, display_title="Concurrent Drug").count() == 1
    assert Prescription.objects.filter(care_activity_id=id1).count() == 1


# ==============================================================================
# 4. AGGREGATE VERSION INVALIDATION (MDS-03: EXACT N -> N+1)
# ==============================================================================


@pytest.mark.django_db
def test_occurrence_skip_increments_version_exactly_once(elder, db):
    wf = _make_wf()
    prescription = create_prescription(
        elder_id=elder.id,
        workflow_definition_id=wf.id,
        recurrence_definition={"type": "daily", "times": ["08:00"]},
        timezone_name="Asia/Tehran",
        start_at=_aware(datetime(2026, 10, 1, 0, 0, tzinfo=ZoneInfo("UTC"))),
        display_title="Skip Test",
        medication_reference="Drug A",
        dosage_information="1 pill",
        elder_friendly_description="Test description",
    )
    activity = prescription.care_activity
    initial_version = activity.aggregate_version

    occurrence = Occurrence.objects.filter(
        schedule_definition_id=activity.schedule_definition_id,
        status=OccurrenceStatus.SCHEDULED,
    ).first()
    assert occurrence is not None

    skip_occurrence(occurrence_id=occurrence.id)
    activity.refresh_from_db()
    # Must increment by EXACTLY 1 (N -> N+1)
    assert activity.aggregate_version == initial_version + 1

    # No-op skip of already skipped occurrence must NOT increment version (N -> N)
    skip_occurrence(occurrence_id=occurrence.id)
    activity.refresh_from_db()
    assert activity.aggregate_version == initial_version + 1


@pytest.mark.django_db
def test_occurrence_cancel_increments_version_exactly_once(elder, db):
    wf = _make_wf()
    prescription = create_prescription(
        elder_id=elder.id,
        workflow_definition_id=wf.id,
        recurrence_definition={"type": "daily", "times": ["08:00"]},
        timezone_name="Asia/Tehran",
        start_at=_aware(datetime(2026, 10, 1, 0, 0, tzinfo=ZoneInfo("UTC"))),
        display_title="Cancel Test",
        medication_reference="Drug B",
        dosage_information="1 pill",
        elder_friendly_description="Test description",
    )
    activity = prescription.care_activity
    initial_version = activity.aggregate_version

    occurrence = Occurrence.objects.filter(
        schedule_definition_id=activity.schedule_definition_id,
        status=OccurrenceStatus.SCHEDULED,
    ).first()
    assert occurrence is not None

    cancel_occurrence(occurrence_id=occurrence.id)
    activity.refresh_from_db()
    # Must increment by EXACTLY 1 (N -> N+1)
    assert activity.aggregate_version == initial_version + 1


@pytest.mark.django_db
def test_schedule_exception_create_and_update_increments_version_exactly_once(elder, db):
    wf = _make_wf()
    prescription = create_prescription(
        elder_id=elder.id,
        workflow_definition_id=wf.id,
        recurrence_definition={"type": "daily", "times": ["08:00", "20:00"]},
        timezone_name="Asia/Tehran",
        start_at=_aware(datetime(2026, 10, 1, 0, 0, tzinfo=ZoneInfo("UTC"))),
        display_title="Exception Test",
        medication_reference="Drug C",
        dosage_information="1 pill",
        elder_friendly_description="Test description",
    )
    activity = prescription.care_activity
    v0 = activity.aggregate_version

    occurrence = Occurrence.objects.filter(
        schedule_definition_id=activity.schedule_definition_id,
        status=OccurrenceStatus.SCHEDULED,
    ).first()
    assert occurrence is not None

    # Step 1: CREATE exception -> must increment by exactly +1 (N -> N+1)
    add_schedule_exception(
        schedule_definition_id=activity.schedule_definition_id,
        original_time=occurrence.scheduled_for,
        exception_type=ScheduleExceptionType.RESCHEDULE,
        replacement_time=occurrence.scheduled_for + timedelta(hours=1),
    )
    activity.refresh_from_db()
    assert activity.aggregate_version == v0 + 1
    v1 = activity.aggregate_version

    # Step 2: UPDATE existing exception -> must increment by exactly +1 (N+1 -> N+2)
    add_schedule_exception(
        schedule_definition_id=activity.schedule_definition_id,
        original_time=occurrence.scheduled_for,
        exception_type=ScheduleExceptionType.RESCHEDULE,
        replacement_time=occurrence.scheduled_for + timedelta(hours=2),
    )
    activity.refresh_from_db()
    assert activity.aggregate_version == v1 + 1


@pytest.mark.django_db
def test_event_replay_does_not_mutate_aggregate_version(elder, db):
    """Replaying an integration event from the outbox MUST NOT mutate aggregate_version."""
    wf = _make_wf()
    prescription = create_prescription(
        elder_id=elder.id,
        workflow_definition_id=wf.id,
        recurrence_definition={"type": "daily", "times": ["08:00"]},
        timezone_name="Asia/Tehran",
        start_at=_aware(datetime(2026, 10, 1, 0, 0, tzinfo=ZoneInfo("UTC"))),
        display_title="Replay Test",
        medication_reference="Drug D",
        dosage_information="1 pill",
        elder_friendly_description="Test description",
    )
    activity = prescription.care_activity
    expected_version = activity.aggregate_version

    ctx = IntegrationContext.new()
    payload = {
        "schedule_definition_id": str(activity.schedule_definition_id),
        "occurrence_id": str(uuid.uuid4()),
        "scheduled_for": timezone.now().isoformat(),
    }

    # Dispatch/replay all 3 integration handlers
    handle_occurrence_skipped(ctx, payload)
    handle_occurrence_cancelled(ctx, payload)
    handle_schedule_exception_added(ctx, payload)

    activity.refresh_from_db()
    assert activity.aggregate_version == expected_version


# ==============================================================================
# 5. END SEMANTICS (C1.5 CONTRACT)
# ==============================================================================


@pytest.mark.django_db
def test_end_care_activity_semantics(elder, db):
    """Ending care activity sets ENDED status on both, cancels future occurrences, and increments version once."""
    wf = _make_wf()
    now = timezone.now()

    prescription = create_prescription(
        elder_id=elder.id,
        workflow_definition_id=wf.id,
        recurrence_definition={"type": "daily", "times": ["08:00", "20:00"]},
        timezone_name="Asia/Tehran",
        start_at=_aware(datetime(2026, 10, 1, 0, 0, tzinfo=ZoneInfo("UTC"))),
        display_title="End Semantics Test",
        medication_reference="Drug E",
        dosage_information="1 pill",
        elder_friendly_description="Test description",
    )
    activity = prescription.care_activity
    v0 = activity.aggregate_version
    schedule_id = activity.schedule_definition_id

    # Create a synthetic past occurrence
    past_occ = Occurrence.objects.create(
        id=uuid.uuid4(),
        schedule_definition_id=schedule_id,
        scheduled_for=now - timedelta(days=2),
        status=OccurrenceStatus.SKIPPED,
    )

    # Future occurrences were generated by create_prescription
    future_occurrences = list(
        Occurrence.objects.filter(
            schedule_definition_id=schedule_id,
            scheduled_for__gte=now,
        )
    )
    assert len(future_occurrences) > 0

    # Call end_care_activity
    ended_activity = end_care_activity(care_activity_id=activity.id)

    # 1. CareActivity status is ENDED
    assert ended_activity.status == CareActivityStatus.ENDED

    # 2. ScheduleDefinition status is ENDED (not CANCELLED)
    schedule = ScheduleDefinition.objects.get(pk=schedule_id)
    assert schedule.status == ScheduleStatus.ENDED

    # 3. Future scheduled occurrences are CANCELLED / suppressed
    for occ in future_occurrences:
        occ.refresh_from_db()
        assert occ.status == OccurrenceStatus.CANCELLED

    # 4. Past occurrences remain unchanged
    past_occ.refresh_from_db()
    assert past_occ.status == OccurrenceStatus.SKIPPED

    # 5. Aggregate version incremented by EXACTLY +1
    ended_activity.refresh_from_db()
    assert ended_activity.aggregate_version == v0 + 1


# ==============================================================================
# 6. ATOMIC PLAN CREATION ROLLBACK
# ==============================================================================


@pytest.mark.django_db
def test_plan_creation_failure_rolls_back_all_entities(elder, monkeypatch, db):
    """P1 failure-injection test: failure during plan creation leaves zero orphaned records."""
    wf = _make_wf()

    # Pre-test baseline
    assert CareActivity.objects.count() == 0
    assert Prescription.objects.count() == 0
    assert ScheduleDefinition.objects.count() == 0
    assert Occurrence.objects.count() == 0
    initial_event_records = EventRecord.objects.count()
    initial_event_outbox = EventOutbox.objects.count()

    # Inject failure into emit_prescription_created (after Schedule, Occurrence, Activity, Prescription are touched)
    def fail_emit(**kwargs):
        raise RuntimeError("Injected failure during prescription event publication.")

    monkeypatch.setattr(
        "domains.care.services.prescriptions.emit_prescription_created",
        fail_emit,
    )

    with pytest.raises(RuntimeError, match="Injected failure"):
        create_prescription(
            elder_id=elder.id,
            workflow_definition_id=wf.id,
            recurrence_definition={"type": "daily", "times": ["08:00"]},
            timezone_name="Asia/Tehran",
            start_at=_aware(datetime(2026, 10, 1, 0, 0, tzinfo=ZoneInfo("UTC"))),
            display_title="Failing Prescription",
            medication_reference="Drug X",
            dosage_information="1 pill",
            elder_friendly_description="Will fail",
        )

    # Verification of 100% clean rollback
    assert Prescription.objects.count() == 0
    assert CareActivity.objects.count() == 0
    assert ScheduleDefinition.objects.count() == 0
    assert Occurrence.objects.count() == 0
    assert EventRecord.objects.count() == initial_event_records
    assert EventOutbox.objects.count() == initial_event_outbox
