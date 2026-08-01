"""Workflow-owned synchronization payload export."""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from domains.workflow.services.executions import get_execution


def _payload_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_workflow_execution_sync_delta(*, execution_id: uuid.UUID) -> dict[str, Any]:
    """Build opaque delta payload owned by Workflow for Synchronization submit."""
    execution = get_execution(execution_id)
    payload = {
        "workflow_execution_id": str(execution.id),
        "occurrence_id": str(execution.occurrence_id),
        "workflow_definition_id": str(execution.workflow_definition_id),
        "status": execution.status,
        "current_step": execution.current_step,
        "aggregate_version": execution.aggregate_version,
    }
    return {
        "aggregate_reference": execution.id,
        "aggregate_version": str(execution.aggregate_version),
        "payload": payload,
        "payload_type": "workflow.execution.delta",
        "payload_hash": _payload_hash(payload),
    }
