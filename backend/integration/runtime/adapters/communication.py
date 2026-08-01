"""Hub communication callback adapter."""

from __future__ import annotations

import uuid

from domains.communication.services.sessions import (
    accept_session,
    end_session,
    record_call_attempt,
    report_attempt_result,
)
from integration.context import IntegrationContext
from integration.observability import logging as integration_logging


def accept_hub_session(ctx: IntegrationContext, *, session_id: uuid.UUID) -> dict[str, str]:
    session = accept_session(session_id=session_id)
    integration_logging.log_orchestration_step(ctx, "hub_session_accepted", session_id=str(session.id))
    return {"session_id": str(session.id), "status": session.status}


def end_hub_session(ctx: IntegrationContext, *, session_id: uuid.UUID) -> dict[str, str]:
    session = end_session(session_id=session_id)
    integration_logging.log_orchestration_step(ctx, "hub_session_ended", session_id=str(session.id))
    return {"session_id": str(session.id), "status": session.status}


def record_hub_call_attempt(ctx: IntegrationContext, *, session_id: uuid.UUID) -> dict[str, str]:
    attempt = record_call_attempt(session_id=session_id)
    return {"attempt_id": str(attempt.id), "attempt_number": attempt.attempt_number}


def report_hub_attempt_result(
    ctx: IntegrationContext,
    *,
    attempt_id: uuid.UUID,
    outcome: str,
    failure_reason: str = "",
) -> dict[str, str]:
    attempt = report_attempt_result(
        attempt_id=attempt_id,
        outcome=outcome,
        failure_reason=failure_reason,
    )
    return {"attempt_id": str(attempt.id), "outcome": attempt.outcome}
