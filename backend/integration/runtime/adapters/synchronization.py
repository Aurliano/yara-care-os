"""Hub synchronization adapter."""

from __future__ import annotations

import uuid
from typing import Any

from domains.synchronization.enums import ReplicaType, SyncDirection
from domains.synchronization.services.operations import submit_aggregate_delta
from domains.synchronization.services.sessions import start_synchronization
from integration.context import IntegrationContext
from integration.exceptions import ReplicaContextRequiredError
from integration.observability import logging as integration_logging


def submit_care_delta_for_replica(
    ctx: IntegrationContext,
    *,
    delta: dict[str, Any],
    idempotency_key: str,
) -> None:
    if ctx.replica_id is None:
        return
    session = start_synchronization(
        replica_identifier=ctx.replica_id,
        replica_type=ReplicaType.HUB,
        direction=SyncDirection.UPLOAD,
        idempotency_key=f"sync-session:{idempotency_key}",
    )
    submit_aggregate_delta(
        session_id=session.id,
        aggregate_reference=delta["aggregate_reference"],
        aggregate_version=delta["aggregate_version"],
        payload=delta["payload"],
        payload_type=delta["payload_type"],
        payload_hash=delta["payload_hash"],
        idempotency_key=idempotency_key,
    )
    integration_logging.log_orchestration_step(
        ctx,
        "sync_delta_submitted",
        session_id=str(session.id),
        aggregate_reference=str(delta["aggregate_reference"]),
    )


def start_upload_session(ctx: IntegrationContext, *, idempotency_key: str):
    if ctx.replica_id is None:
        raise ReplicaContextRequiredError("replica_id is required")
    return start_synchronization(
        replica_identifier=ctx.replica_id,
        replica_type=ReplicaType.HUB,
        direction=SyncDirection.UPLOAD,
        idempotency_key=idempotency_key,
    )


def start_download_session(ctx: IntegrationContext, *, idempotency_key: str):
    if ctx.replica_id is None:
        raise ReplicaContextRequiredError("replica_id is required")
    return start_synchronization(
        replica_identifier=ctx.replica_id,
        replica_type=ReplicaType.BACKEND,
        direction=SyncDirection.DOWNLOAD,
        idempotency_key=idempotency_key,
    )


def complete_download_session(ctx: IntegrationContext, *, session_id: uuid.UUID) -> dict[str, Any]:
    if ctx.replica_id is None:
        raise ReplicaContextRequiredError("replica_id is required")
    from integration.services.hub_download_staging import complete_hub_download_session

    result = complete_hub_download_session(ctx=ctx, session_id=session_id)
    integration_logging.log_orchestration_step(
        ctx,
        "sync_download_completed",
        session_id=str(session_id),
        operations_applied=result.get("operations_applied", 0),
    )
    return result
