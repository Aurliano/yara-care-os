import uuid
from datetime import timedelta

import pytest
from django.db import transaction
from django.utils import timezone

from domains.event.enums import OutboxStatus
from domains.event.exceptions import DuplicateEventError, EventImmutabilityError
from domains.event.models import EventOutbox, EventRecord
from domains.event.services.queries import (
    get_event,
    get_events_by_correlation,
    get_events_by_producer,
    get_events_since,
)
from domains.event.services.recording import EventInput, publish_event, record_event


def _event_input(**overrides) -> EventInput:
    defaults = {
        "event_id": uuid.uuid4(),
        "event_type": "LicenseActivated",
        "event_version": 1,
        "producer": "licensing",
        "occurred_at": timezone.now() - timedelta(hours=2),
        "payload": {"plan_code": "PLUS"},
        "correlation_id": "corr-123",
        "causation_id": "cause-456",
    }
    defaults.update(overrides)
    return EventInput(**defaults)


@pytest.mark.django_db
def test_event_id_uniqueness():
    event_input = _event_input()
    record_event(event_input)
    with pytest.raises(EventImmutabilityError):
        EventRecord.objects.create(
            id=event_input.event_id,
            event_type="Duplicate",
            event_version=1,
            producer="other",
            occurred_at=timezone.now(),
            payload={},
        )


@pytest.mark.django_db
def test_event_record_creation():
    event_input = _event_input()
    event = record_event(event_input)
    assert event.event_type == "LicenseActivated"
    assert event.event_version == 1
    assert event.producer == "licensing"
    assert event.payload == {"plan_code": "PLUS"}
    assert EventOutbox.objects.filter(event=event, status=OutboxStatus.PENDING).exists()


@pytest.mark.django_db
def test_recorded_events_are_immutable():
    event = record_event(_event_input())
    event.payload = {"changed": True}
    with pytest.raises(EventImmutabilityError):
        event.save()


@pytest.mark.django_db
def test_occurred_at_independent_of_recorded_at():
    occurred = timezone.now() - timedelta(days=3)
    event = record_event(_event_input(occurred_at=occurred))
    assert event.occurred_at == occurred
    assert event.recorded_at > occurred


@pytest.mark.django_db
def test_correlation_and_causation_metadata():
    event = record_event(_event_input(correlation_id="flow-1", causation_id="cmd-9"))
    assert event.correlation_id == "flow-1"
    assert event.causation_id == "cmd-9"


@pytest.mark.django_db
def test_correlation_queries():
    correlation_id = "shared-flow"
    first = record_event(_event_input(correlation_id=correlation_id))
    second = record_event(_event_input(correlation_id=correlation_id))
    results = get_events_by_correlation(correlation_id)
    assert len(results) == 2
    assert {event.id for event in results} == {first.id, second.id}


@pytest.mark.django_db
def test_producer_query():
    record_event(_event_input(producer="licensing"))
    record_event(_event_input(producer="device"))
    licensing_events = get_events_by_producer("licensing")
    assert len(licensing_events) == 1
    assert licensing_events[0].producer == "licensing"


@pytest.mark.django_db
def test_get_events_since():
    old = record_event(_event_input(occurred_at=timezone.now() - timedelta(days=5)))
    recent = record_event(_event_input(occurred_at=timezone.now() - timedelta(hours=1)))
    results = get_events_since(since=timezone.now() - timedelta(days=2))
    assert recent.id in {event.id for event in results}
    assert old.id not in {event.id for event in results}


@pytest.mark.django_db
def test_idempotent_record_by_event_id():
    event_input = _event_input()
    first = record_event(event_input)
    second = record_event(event_input)
    assert first.id == second.id
    assert EventRecord.objects.count() == 1
    assert EventOutbox.objects.count() == 1


@pytest.mark.django_db
def test_duplicate_event_id_with_different_data_rejected():
    event_input = _event_input()
    record_event(event_input)
    different = EventInput(
        event_id=event_input.event_id,
        event_type="DifferentType",
        event_version=1,
        producer="licensing",
        occurred_at=event_input.occurred_at,
        payload={},
    )
    with pytest.raises(DuplicateEventError):
        record_event(different)


@pytest.mark.django_db
def test_publish_event_is_idempotent():
    event = record_event(_event_input())
    first = publish_event(event_id=event.id)
    second = publish_event(event_id=event.id)
    assert first.status == OutboxStatus.PUBLISHED
    assert second.status == OutboxStatus.PUBLISHED
    assert EventOutbox.objects.filter(event=event).count() == 1


@pytest.mark.django_db
def test_outbox_created_transactionally_with_event():
    event_input = _event_input()
    with transaction.atomic():
        event = record_event(event_input)
        assert EventOutbox.objects.filter(event=event).exists()


@pytest.mark.django_db
def test_minimal_payload_persistence():
    event = record_event(_event_input(payload={"status": "ACTIVE"}))
    stored = get_event(event.id)
    assert stored.payload == {"status": "ACTIVE"}


@pytest.mark.django_db
def test_event_record_has_no_domain_reference_fields():
    event = record_event(_event_input())
    field_names = {field.name for field in EventRecord._meta.get_fields()}
    forbidden = {"elder_id", "device_id", "execution_id", "occurrence_id", "entity_type", "entity_id"}
    assert forbidden.isdisjoint(field_names)
