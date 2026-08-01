"""Default workflow action handlers."""

from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Any

from django.utils import timezone

from domains.device.enums import AssignmentStatus, CommandType
from domains.device.services.assignments import get_assignments
from domains.device.services.commands import create_device_command, deliver_command
from domains.communication.enums import CommunicationChannel
from domains.communication.services.contacts import get_priority_contacts
from domains.communication.services.sessions import initiate_session
from domains.workflow.enums import ActionType
from integration.context import IntegrationContext
from integration.runtime.action_handlers.registry import REGISTRY, ActionHandler


class ShowReminderHandler:
    action_type = ActionType.SHOW_REMINDER

    def handle(self, ctx: IntegrationContext, *, payload: dict[str, Any]) -> None:
        dispatch_context = payload.get("dispatch_context") or {}
        elder_id = uuid.UUID(dispatch_context["elder_id"])
        execution_id = uuid.UUID(payload["workflow_execution_id"])
        assignments = get_assignments(elder_id=elder_id)
        hub_assignment = next((a for a in assignments if a.status == AssignmentStatus.ASSIGNED), None)
        if hub_assignment is None:
            return
        device_id = hub_assignment.device_id
        ctx = ctx.with_device(device_id).with_execution(execution_id)
        command = create_device_command(
            target_device_id=device_id,
            command_type=CommandType.SHOW_DISPLAY,
            idempotency_key=f"reminder:{execution_id}:{payload.get('current_step', 'initial')}",
            expires_at=timezone.now() + timedelta(hours=1),
            parameters={"workflow_execution_id": str(execution_id)},
            execution_reference=execution_id,
        )
        deliver_command(command_id=command.id)


class InitiateCallHandler:
    action_type = ActionType.INITIATE_CALL

    def handle(self, ctx: IntegrationContext, *, payload: dict[str, Any]) -> None:
        dispatch_context = payload.get("dispatch_context") or {}
        elder_id = uuid.UUID(dispatch_context["elder_id"])
        execution_id = uuid.UUID(payload["workflow_execution_id"])
        contacts = get_priority_contacts(elder_id=elder_id)
        if not contacts:
            return
        recipient = contacts[0]
        initiate_session(
            elder_id=elder_id,
            channel=CommunicationChannel.VOICE,
            initiator_user_id=ctx.actor_id,
            recipient_contact_id=recipient.id,
            external_execution_reference=execution_id,
        )


def register_default_handlers() -> None:
    REGISTRY.register(ShowReminderHandler())
    REGISTRY.register(InitiateCallHandler())
