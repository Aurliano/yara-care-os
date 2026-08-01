"""Integration event dispatcher."""

from __future__ import annotations

import uuid

from django.db import IntegrityError, transaction

from domains.event.services.queries import get_event, list_recent_events
from integration.context import IntegrationContext
from integration.handlers.events import EVENT_HANDLERS
from integration.models import ProcessedIntegrationEvent
from integration.observability import logging as integration_logging
from integration.observability.metrics import increment

# Safety rail: cap drain loops so a runaway event chain cannot spin forever.
MAX_DISPATCH_ITERATIONS = 50


def _handler_name(event_type: str) -> str:
    return event_type


def _already_processed(*, event_id: uuid.UUID, handler_name: str) -> bool:
    return ProcessedIntegrationEvent.objects.filter(
        event_id=event_id,
        handler_name=handler_name,
    ).exists()


@transaction.atomic
def _mark_processed(*, event_id: uuid.UUID, handler_name: str) -> None:
    try:
        ProcessedIntegrationEvent.objects.create(event_id=event_id, handler_name=handler_name)
    except IntegrityError:
        return


def process_event(ctx: IntegrationContext, event_id: uuid.UUID) -> bool:
    event = get_event(event_id)
    handler = EVENT_HANDLERS.get(event.event_type)
    if handler is None:
        return False

    handler_name = _handler_name(event.event_type)
    if _already_processed(event_id=event_id, handler_name=handler_name):
        increment("integration.event.duplicate_skipped")
        return False

    if event.correlation_id:
        ctx = IntegrationContext(
            correlation_id=event.correlation_id,
            execution_id=ctx.execution_id,
            replica_id=ctx.replica_id,
            actor_id=ctx.actor_id,
            device_id=ctx.device_id,
        )

    payload = dict(event.payload)
    payload["event_id"] = str(event.id)
    integration_logging.log_orchestration_step(
        ctx,
        "event_dispatch",
        event_type=event.event_type,
        handler_name=handler_name,
    )
    handler(ctx, payload)
    _mark_processed(event_id=event_id, handler_name=handler_name)
    increment("integration.event.processed")
    return True


def process_pending_events(
    ctx: IntegrationContext,
    *,
    limit: int = 100,
    max_iterations: int = MAX_DISPATCH_ITERATIONS,
) -> int:
    total = 0
    for iteration in range(max_iterations):
        processed_keys = set(
            ProcessedIntegrationEvent.objects.values_list("event_id", "handler_name")
        )
        batch = 0
        for event in list_recent_events(limit=limit):
            handler_name = _handler_name(event.event_type)
            if (event.id, handler_name) in processed_keys:
                continue
            if process_event(ctx, event.id):
                batch += 1
        total += batch
        if batch == 0:
            return total

    integration_logging.log_orchestration_step(
        ctx,
        "event_dispatch_iteration_limit",
        max_iterations=max_iterations,
        processed_total=total,
    )
    increment("integration.event.dispatch_iteration_limit")
    return total
