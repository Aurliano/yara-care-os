"""Deterministic Care domain identity helpers."""

from __future__ import annotations

import uuid

from domains.care.constants import CARE_NAMESPACE


def compute_care_event_id(
    *,
    event_type: str,
    subject_id: uuid.UUID,
    discriminator: str = "",
) -> uuid.UUID:
    """Stable event identity for one Care business fact."""
    key = f"{event_type}:{subject_id}"
    if discriminator:
        key = f"{key}:{discriminator}"
    return uuid.uuid5(CARE_NAMESPACE, key)


def compute_care_completion_id(*, workflow_execution_id: uuid.UUID) -> uuid.UUID:
    """Stable CareCompletion identity for one WorkflowExecution result."""
    return uuid.uuid5(CARE_NAMESPACE, f"completion:{workflow_execution_id}")
