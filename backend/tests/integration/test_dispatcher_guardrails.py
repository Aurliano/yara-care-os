"""Runtime guardrail tests for integration dispatcher."""

import uuid

import pytest
from django.db import IntegrityError

from integration.context import IntegrationContext
from integration.models import ProcessedIntegrationEvent
from integration.runtime.dispatcher import process_pending_events
from integration.observability.metrics import METRICS, snapshot


@pytest.mark.django_db
def test_processed_event_unique_per_handler_name():
    event_id = uuid.uuid4()
    ProcessedIntegrationEvent.objects.create(event_id=event_id, handler_name="ExecutionStarted")
    ProcessedIntegrationEvent.objects.create(event_id=event_id, handler_name="ExecutionConfirmed")
    assert ProcessedIntegrationEvent.objects.filter(event_id=event_id).count() == 2

    with pytest.raises(IntegrityError):
        ProcessedIntegrationEvent.objects.create(event_id=event_id, handler_name="ExecutionStarted")


@pytest.mark.django_db
def test_process_pending_events_stops_at_iteration_limit(monkeypatch):
    from integration.runtime import dispatcher as dispatcher_module

    METRICS.clear()
    event_id = uuid.uuid4()

    class FakeEvent:
        id = event_id
        event_type = "ExecutionStarted"

    monkeypatch.setattr(
        dispatcher_module,
        "list_recent_events",
        lambda limit=100: [FakeEvent()],
    )
    monkeypatch.setattr(dispatcher_module, "process_event", lambda ctx, eid: True)

    total = process_pending_events(IntegrationContext.new(), limit=10, max_iterations=5)
    assert total == 5
    assert snapshot().get("integration.event.dispatch_iteration_limit") == 1


@pytest.mark.django_db
def test_f06_handler_unexpected_failure_does_not_block_subsequent_events(monkeypatch):
    """Prove F-06 resolution: Unexpected exception in Event A does not starve Event B."""
    from datetime import datetime, timezone
    from domains.event.models import EventRecord
    from integration.handlers import events as events_module
    from integration.runtime.dispatcher import list_pending_integration_events

    METRICS.clear()
    ctx = IntegrationContext.new()

    # Create real event A (older) and event B (newer)
    event_a = EventRecord.objects.create(
        event_type="ExecutionStarted",
        event_version=1,
        producer="test",
        occurred_at=datetime(2026, 9, 20, 10, 0, tzinfo=timezone.utc),
        payload={"workflow_execution_id": str(uuid.uuid4())},
    )
    event_b = EventRecord.objects.create(
        event_type="ExecutionConfirmed",
        event_version=1,
        producer="test",
        occurred_at=datetime(2026, 9, 20, 10, 5, tzinfo=timezone.utc),
        payload={"workflow_execution_id": str(uuid.uuid4())},
    )

    # Event A handler raises unexpected unhandled exception
    def failing_handler(ctx, payload):
        raise RuntimeError("Unexpected failure inside registered handler (F-06 scenario)")

    handled_b = []

    def succeeding_handler(ctx, payload):
        handled_b.append(payload["event_id"])

    monkeypatch.setitem(events_module.EVENT_HANDLERS, "ExecutionStarted", failing_handler)
    monkeypatch.setitem(events_module.EVENT_HANDLERS, "ExecutionConfirmed", succeeding_handler)

    # Dispatch pending events
    total_processed = process_pending_events(ctx, limit=10)

    # Event B succeeded!
    assert total_processed == 1
    assert str(event_b.id) in handled_b

    # Both events are recorded in ProcessedIntegrationEvent:
    # Event A via explicit terminal handling, Event B via success
    assert ProcessedIntegrationEvent.objects.filter(event_id=event_a.id, handler_name="ExecutionStarted").exists()
    assert ProcessedIntegrationEvent.objects.filter(event_id=event_b.id, handler_name="ExecutionConfirmed").exists()

    # Metrics confirm 1 terminal failure and 1 successful processing
    assert snapshot().get("integration.event.terminal_failure") == 1
    assert snapshot().get("integration.event.processed") == 1

    # Queue is completely clear: zero pending events remain
    assert len(list_pending_integration_events()) == 0


@pytest.mark.django_db
def test_f06_retryable_exception_bounded_retry_and_exhaustion(monkeypatch):
    """Prove that retryable errors retry up to MAX_EVENT_RETRIES before terminal handling."""
    from datetime import datetime, timezone
    from django.db import OperationalError
    from domains.event.models import EventRecord
    from integration.handlers import events as events_module
    from integration.runtime.dispatcher import _RETRY_COUNTS, MAX_EVENT_RETRIES

    METRICS.clear()
    _RETRY_COUNTS.clear()
    ctx = IntegrationContext.new()

    event = EventRecord.objects.create(
        event_type="ExecutionStarted",
        event_version=1,
        producer="test",
        occurred_at=datetime(2026, 9, 20, 10, 0, tzinfo=timezone.utc),
        payload={"workflow_execution_id": str(uuid.uuid4())},
    )

    def transient_failure(ctx, payload):
        raise OperationalError("Transient DB connection error")

    monkeypatch.setitem(events_module.EVENT_HANDLERS, "ExecutionStarted", transient_failure)

    # First attempt: retry scheduled, not yet marked processed in DB
    process_pending_events(ctx, limit=10, max_iterations=1)
    assert not ProcessedIntegrationEvent.objects.filter(event_id=event.id).exists()
    assert snapshot().get("integration.event.retry_scheduled") == 1

    # Second attempt
    process_pending_events(ctx, limit=10, max_iterations=1)
    assert not ProcessedIntegrationEvent.objects.filter(event_id=event.id).exists()
    assert snapshot().get("integration.event.retry_scheduled") == 2

    # Third attempt: max retries reached -> terminally handled
    process_pending_events(ctx, limit=10, max_iterations=1)
    assert ProcessedIntegrationEvent.objects.filter(event_id=event.id, handler_name="ExecutionStarted").exists()
    assert snapshot().get("integration.event.retries_exhausted") == 1
