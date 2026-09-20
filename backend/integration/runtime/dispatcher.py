"""Integration event dispatcher."""

from __future__ import annotations

import uuid

from django.db import IntegrityError, transaction
from django.db.models import Exists, OuterRef

from domains.event.models import EventRecord
from domains.event.services.queries import get_event
from integration.context import IntegrationContext
from integration.handlers.events import EVENT_HANDLERS
from integration.models import ProcessedIntegrationEvent
from integration.observability import logging as integration_logging
from integration.observability.metrics import increment

# Safety rail: cap drain loops so a runaway event chain cannot spin forever.
MAX_DISPATCH_ITERATIONS = 50
MAX_EVENT_RETRIES = 3

_RETRY_COUNTS: dict[uuid.UUID, int] = {}


def is_retryable_exception(exc: Exception) -> bool:
    """Classify transient infrastructure exceptions as retryable.

    Domain logic errors, schema errors, and validation errors are non-retryable.
    """
    from django.db import OperationalError
    return isinstance(exc, OperationalError)


def list_pending_integration_events(*, limit: int = 100) -> list[EventRecord]:
    """Fetch only un-dispatched events whose event_type matches registered EVENT_HANDLERS."""
    processed_subquery = ProcessedIntegrationEvent.objects.filter(
        event_id=OuterRef("pk"),
        handler_name=OuterRef("event_type"),
    )
    return list(
        EventRecord.objects.filter(event_type__in=EVENT_HANDLERS.keys())
        .annotate(already_processed=Exists(processed_subquery))
        .filter(already_processed=False)
        .order_by("recorded_at")[:limit]
    )


# Default provider for event fetching in dispatcher loop; alias preserved for tests monkeypatching list_recent_events
list_recent_events = list_pending_integration_events


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
    handler_name = _handler_name(event.event_type)
    if handler is None:
        _mark_processed(event_id=event_id, handler_name=handler_name)
        return False
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
        event_id=str(event.id),
    )
    try:
        handler(ctx, payload)
    except Exception as exc:  # noqa: BLE001 — dispatcher-level fallback for F-06
        if is_retryable_exception(exc):
            attempts = _RETRY_COUNTS.get(event.id, 0) + 1
            _RETRY_COUNTS[event.id] = attempts
            if attempts < MAX_EVENT_RETRIES:
                integration_logging.log_orchestration_step(
                    ctx,
                    "event_dispatch_retry_scheduled",
                    event_id=str(event.id),
                    event_type=event.event_type,
                    attempt=attempts,
                    error=str(exc),
                )
                increment("integration.event.retry_scheduled")
                return False
            _RETRY_COUNTS.pop(event.id, None)
            integration_logging.log_orchestration_step(
                ctx,
                "event_dispatch_retries_exhausted",
                event_id=str(event.id),
                event_type=event.event_type,
                attempts=attempts,
                error=str(exc),
            )
            increment("integration.event.retries_exhausted")
        else:
            integration_logging.log_orchestration_step(
                ctx,
                "event_dispatch_terminal_failure",
                event_id=str(event.id),
                event_type=event.event_type,
                error=str(exc),
            )
            increment("integration.event.terminal_failure")

        # Explicit terminal handling: mark processed so dead events cannot head-of-line block subsequent events
        _mark_processed(event_id=event_id, handler_name=handler_name)
        return False

    _RETRY_COUNTS.pop(event.id, None)
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
    for _iteration in range(max_iterations):
        recent_events = list_recent_events(limit=limit)
        if not recent_events:
            break
        event_ids = [event.id for event in recent_events]
        processed_keys = set(
            ProcessedIntegrationEvent.objects.filter(event_id__in=event_ids).values_list(
                "event_id",
                "handler_name",
            )
        )
        batch = 0
        for event in recent_events:
            handler_name = _handler_name(event.event_type)
            if (event.id, handler_name) in processed_keys:
                continue
            try:
                if process_event(ctx, event.id):
                    batch += 1
            except Exception as exc:  # noqa: BLE001 — safety net for outer loop
                integration_logging.log_orchestration_step(
                    ctx,
                    "event_dispatch_outer_unexpected_error",
                    event_id=str(event.id),
                    error=str(exc),
                )
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
