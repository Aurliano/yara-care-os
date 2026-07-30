"""Deterministic workflow identity helpers."""

from __future__ import annotations

import uuid

from domains.workflow.constants import WORKFLOW_NAMESPACE


def compute_execution_id(*, occurrence_id: uuid.UUID) -> uuid.UUID:
    """Stable WorkflowExecution identity for one Scheduling Occurrence."""
    return uuid.uuid5(WORKFLOW_NAMESPACE, f"execution:{occurrence_id}")


def compute_workflow_event_id(*, event_type: str, subject_id: uuid.UUID) -> uuid.UUID:
    """Stable event identity for one Workflow fact."""
    return uuid.uuid5(WORKFLOW_NAMESPACE, f"{event_type}:{subject_id}")
