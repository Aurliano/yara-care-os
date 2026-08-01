"""Workflow aggregate version ownership for synchronization."""

from __future__ import annotations

from domains.workflow.models import WorkflowExecution


def bump_workflow_execution_version(execution: WorkflowExecution, update_fields: list[str]) -> list[str]:
    """Increment monotonic aggregate version owned by Workflow."""
    execution.aggregate_version += 1
    if "aggregate_version" not in update_fields:
        update_fields.append("aggregate_version")
    return update_fields
