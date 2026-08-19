"""Hub device callback adapter."""

from __future__ import annotations

import uuid
from typing import Any

from domains.device.services.commands import complete_command, deliver_command, fail_command, get_command_status
from domains.device.services.devices import get_device, update_device_state
from integration.context import IntegrationContext
from integration.observability import logging as integration_logging


def update_hub_device_state(
    ctx: IntegrationContext,
    *,
    device_id: uuid.UUID,
    current_state: dict[str, Any],
    is_online: bool | None = None,
) -> dict[str, Any]:
    ctx = ctx.with_device(device_id)
    existing = get_device(device_id)
    previous = (existing.current_state or {}).get("network")
    merged = dict(existing.current_state or {})
    merged.update(current_state)
    emit_online = is_online
    if is_online is True and previous == "online":
        emit_online = None
    elif is_online is False and previous == "offline":
        emit_online = None
    device = update_device_state(device_id=device_id, current_state=merged, is_online=emit_online)
    integration_logging.log_orchestration_step(ctx, "hub_device_state_updated")
    return {"device_id": str(device.id), "operational_status": device.operational_status}


def deliver_hub_command(ctx: IntegrationContext, *, command_id: uuid.UUID) -> dict[str, str]:
    status_info = get_command_status(command_id)
    ctx = ctx.with_device(uuid.UUID(status_info["target_device_id"]))
    command = deliver_command(command_id=command_id)
    integration_logging.log_orchestration_step(ctx, "hub_command_delivered", command_id=str(command.id))
    return {"command_id": str(command.id), "status": command.status}


def complete_hub_command(
    ctx: IntegrationContext,
    *,
    command_id: uuid.UUID,
    result: dict[str, Any] | None = None,
) -> dict[str, str]:
    command = complete_command(command_id=command_id, result=result)
    integration_logging.log_orchestration_step(ctx, "hub_command_completed", command_id=str(command.id))
    return {"command_id": str(command.id), "status": command.status}


def fail_hub_command(ctx: IntegrationContext, *, command_id: uuid.UUID, reason: str = "") -> dict[str, str]:
    command = fail_command(command_id=command_id, failure_reason=reason)
    integration_logging.log_orchestration_step(ctx, "hub_command_failed", command_id=str(command.id))
    return {"command_id": str(command.id), "status": command.status}
