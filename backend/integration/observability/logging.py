"""Structured logging for integration orchestration."""

from __future__ import annotations

import logging
from typing import Any

from integration.context import IntegrationContext

logger = logging.getLogger("yara.integration")


def log_orchestration_step(ctx: IntegrationContext, step: str, **extra: Any) -> None:
    logger.info(
        step,
        extra={
            "correlation_id": ctx.correlation_id,
            "execution_id": str(ctx.execution_id) if ctx.execution_id else None,
            "replica_id": str(ctx.replica_id) if ctx.replica_id else None,
            "actor_id": str(ctx.actor_id) if ctx.actor_id else None,
            "device_id": str(ctx.device_id) if ctx.device_id else None,
            **extra,
        },
    )
