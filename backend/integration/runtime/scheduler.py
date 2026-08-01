"""Integration runtime schedulers."""

from __future__ import annotations

from domains.scheduling.services.due import process_due_occurrences
from domains.workflow.services.timeout import process_workflow_timeouts
from integration.context import IntegrationContext
from integration.runtime.dispatcher import process_pending_events


def run_due_occurrence_scan(ctx: IntegrationContext) -> int:
    return process_due_occurrences()


def run_workflow_timeout_scan(ctx: IntegrationContext) -> int:
    return process_workflow_timeouts()


def run_event_dispatch(ctx: IntegrationContext, *, limit: int = 100) -> int:
    return process_pending_events(ctx, limit=limit)


def run_integration_cycle(ctx: IntegrationContext, *, event_limit: int = 100) -> dict[str, int]:
    return {
        "due_occurrences": run_due_occurrence_scan(ctx),
        "workflow_timeouts": run_workflow_timeout_scan(ctx),
        "events_processed": run_event_dispatch(ctx, limit=event_limit),
    }
