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
