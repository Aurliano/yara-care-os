"""Hub confirmation callback adapter."""

from __future__ import annotations

import uuid

from domains.workflow.services.evidence import submit_direct_interaction_evidence
from integration.context import IntegrationContext
from integration.observability import logging as integration_logging


def submit_hub_confirmation(
    ctx: IntegrationContext,
    *,
    execution_id: uuid.UUID,
    interaction_reference: str,
    evidence_type: str = "HUB_CONFIRMATION",
    actor_user_id: uuid.UUID | None = None,
) -> dict[str, str]:
    ctx = ctx.with_execution(execution_id)
    execution = submit_direct_interaction_evidence(
        execution_id=execution_id,
        evidence_type=evidence_type,
        interaction_reference=interaction_reference,
        actor_user_id=actor_user_id or ctx.actor_id,
    )
    integration_logging.log_orchestration_step(ctx, "hub_confirmation_submitted")
    return {"workflow_execution_id": str(execution.id), "status": execution.status}
