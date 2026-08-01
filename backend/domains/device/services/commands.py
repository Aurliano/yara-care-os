"""DeviceCommand aggregate lifecycle."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from django.db import IntegrityError, transaction
from django.utils import timezone

from domains.device.enums import TERMINAL_COMMAND_STATUSES, CommandStatus, CommandType
from domains.device.exceptions import DeviceCommandNotFoundError, InvalidCommandStateError
from domains.device.identity import compute_command_id
from domains.device.models import DeviceCommand
from domains.device.services.devices import ensure_device_accepts_commands, get_device
from domains.device.services.events import emit_device_command_completed, emit_device_command_failed


def get_command(command_id: uuid.UUID) -> DeviceCommand:
    try:
        return DeviceCommand.objects.select_related("target_device").get(pk=command_id)
    except DeviceCommand.DoesNotExist as exc:
        raise DeviceCommandNotFoundError("Device command not found.") from exc


def get_command_status(command_id: uuid.UUID) -> dict[str, Any]:
    command = get_command(command_id)
    return {
        "command_id": str(command.id),
        "status": command.status,
        "command_type": command.command_type,
        "target_device_id": str(command.target_device_id),
        "execution_reference": str(command.execution_reference) if command.execution_reference else None,
        "completed_at": command.completed_at.isoformat() if command.completed_at else None,
    }


def get_commands(
    *,
    device_id: uuid.UUID | None = None,
    execution_reference: uuid.UUID | None = None,
) -> list[DeviceCommand]:
    queryset = DeviceCommand.objects.select_related("target_device").order_by("-created_at")
    if device_id is not None:
        queryset = queryset.filter(target_device_id=device_id)
    if execution_reference is not None:
        queryset = queryset.filter(execution_reference=execution_reference)
    return list(queryset)


def _ensure_not_terminal(command: DeviceCommand) -> None:
    if command.status in TERMINAL_COMMAND_STATUSES:
        raise InvalidCommandStateError("Terminal commands cannot be modified.")


def _ensure_not_expired(command: DeviceCommand, *, now: datetime | None = None) -> None:
    now = now or timezone.now()
    if command.expires_at <= now and command.status not in TERMINAL_COMMAND_STATUSES:
        command.status = CommandStatus.EXPIRED
        command.completed_at = now
        command.save(update_fields=["status", "completed_at"])
        raise InvalidCommandStateError("Command has expired.")


@transaction.atomic
def create_device_command(
    *,
    target_device_id: uuid.UUID,
    command_type: str,
    idempotency_key: str,
    expires_at: datetime,
    parameters: dict[str, Any] | None = None,
    execution_reference: uuid.UUID | None = None,
) -> DeviceCommand:
    if command_type not in CommandType.values:
        raise InvalidCommandStateError("Invalid command type.")

    device = get_device(target_device_id)
    ensure_device_accepts_commands(device)

    command_id = compute_command_id(idempotency_key=idempotency_key)
    existing = DeviceCommand.objects.filter(pk=command_id).first()
    if existing is not None:
        return existing

    try:
        return DeviceCommand.objects.create(
            id=command_id,
            target_device=device,
            command_type=command_type,
            parameters=parameters or {},
            status=CommandStatus.QUEUED,
            expires_at=expires_at,
            idempotency_key=idempotency_key,
            execution_reference=execution_reference,
        )
    except IntegrityError:
        return DeviceCommand.objects.get(idempotency_key=idempotency_key)


@transaction.atomic
def deliver_command(*, command_id: uuid.UUID) -> DeviceCommand:
    command = DeviceCommand.objects.select_for_update().get(pk=command_id)
    if command.status in TERMINAL_COMMAND_STATUSES:
        return command

    _ensure_not_expired(command)

    if command.status == CommandStatus.QUEUED:
        now = timezone.now()
        command.status = CommandStatus.DELIVERED
        command.delivered_at = now
        command.save(update_fields=["status", "delivered_at"])
    return command


@transaction.atomic
def start_command_execution(*, command_id: uuid.UUID) -> DeviceCommand:
    command = DeviceCommand.objects.select_for_update().get(pk=command_id)
    if command.status in TERMINAL_COMMAND_STATUSES:
        if command.status in {CommandStatus.SUCCEEDED, CommandStatus.EXECUTING}:
            return command
        raise InvalidCommandStateError("Terminal commands cannot be started.")

    if command.status not in {CommandStatus.DELIVERED, CommandStatus.EXECUTING}:
        if command.status == CommandStatus.QUEUED:
            command = deliver_command(command_id=command.id)
            command = DeviceCommand.objects.select_for_update().get(pk=command.id)
        else:
            raise InvalidCommandStateError("Command must be delivered before execution.")

    if command.status == CommandStatus.EXECUTING:
        return command

    now = timezone.now()
    command.status = CommandStatus.EXECUTING
    command.executing_at = now
    command.save(update_fields=["status", "executing_at"])
    return command


@transaction.atomic
def complete_command(
    *,
    command_id: uuid.UUID,
    result: dict[str, Any] | None = None,
) -> DeviceCommand:
    command = DeviceCommand.objects.select_for_update().get(pk=command_id)
    if command.status == CommandStatus.SUCCEEDED:
        return command

    if command.status in {CommandStatus.FAILED, CommandStatus.EXPIRED, CommandStatus.CANCELLED}:
        raise InvalidCommandStateError("Terminal commands cannot be completed.")

    _ensure_not_expired(command)

    if command.status != CommandStatus.EXECUTING:
        start_command_execution(command_id=command.id)
        command = DeviceCommand.objects.select_for_update().get(pk=command.id)

    now = timezone.now()
    command.status = CommandStatus.SUCCEEDED
    command.result = result or {}
    command.completed_at = now
    command.save(update_fields=["status", "result", "completed_at"])
    emit_device_command_completed(
        command_id=command.id,
        device_id=command.target_device_id,
        command_type=command.command_type,
        execution_reference=command.execution_reference,
    )
    return command


@transaction.atomic
def fail_command(*, command_id: uuid.UUID, failure_reason: str = "") -> DeviceCommand:
    command = DeviceCommand.objects.select_for_update().get(pk=command_id)
    if command.status in {CommandStatus.SUCCEEDED, CommandStatus.FAILED, CommandStatus.EXPIRED, CommandStatus.CANCELLED}:
        if command.status == CommandStatus.FAILED:
            return command
        raise InvalidCommandStateError("Terminal commands cannot fail again.")

    _ensure_not_expired(command)

    now = timezone.now()
    command.status = CommandStatus.FAILED
    command.failure_reason = failure_reason
    command.completed_at = now
    command.save(update_fields=["status", "failure_reason", "completed_at"])
    emit_device_command_failed(
        command_id=command.id,
        device_id=command.target_device_id,
        reason=failure_reason,
    )
    return command


@transaction.atomic
def cancel_command(*, command_id: uuid.UUID) -> DeviceCommand:
    command = DeviceCommand.objects.select_for_update().get(pk=command_id)
    if command.status in TERMINAL_COMMAND_STATUSES:
        return command

    now = timezone.now()
    command.status = CommandStatus.CANCELLED
    command.completed_at = now
    command.save(update_fields=["status", "completed_at"])
    return command


@transaction.atomic
def expire_command(*, command_id: uuid.UUID) -> DeviceCommand:
    command = DeviceCommand.objects.select_for_update().get(pk=command_id)
    if command.status in TERMINAL_COMMAND_STATUSES:
        return command

    now = timezone.now()
    if command.expires_at > now:
        raise InvalidCommandStateError("Command has not reached expiration time.")

    command.status = CommandStatus.EXPIRED
    command.completed_at = now
    command.save(update_fields=["status", "completed_at"])
    return command
