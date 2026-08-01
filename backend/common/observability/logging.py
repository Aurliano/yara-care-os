"""Shared structured logging helpers."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID


def _stringify(value: UUID | str | None) -> str | None:
    if value is None:
        return None
    return str(value)


def log_structured(
    logger: logging.Logger,
    message: str,
    *,
    correlation_id: str | None = None,
    execution_id: UUID | str | None = None,
    event_id: UUID | str | None = None,
    replica_id: UUID | str | None = None,
    device_id: UUID | str | None = None,
    session_id: UUID | str | None = None,
    command_id: UUID | str | None = None,
    **extra: Any,
) -> None:
    """Emit structured log context without secrets."""
    logger.info(
        message,
        extra={
            "correlation_id": correlation_id,
            "execution_id": _stringify(execution_id),
            "event_id": _stringify(event_id),
            "replica_id": _stringify(replica_id),
            "device_id": _stringify(device_id),
            "session_id": _stringify(session_id),
            "command_id": _stringify(command_id),
            **extra,
        },
    )
