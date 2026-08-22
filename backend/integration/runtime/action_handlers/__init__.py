"""Default workflow action handlers."""

from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Any

from django.utils import timezone

from domains.care.services.activities import get_care_activity_for_schedule
from domains.communication.enums import CommunicationChannel
from domains.communication.services.contacts import get_priority_contacts
from domains.communication.services.sessions import initiate_session
from domains.device.enums import AssignmentStatus, CommandType
from domains.device.services.assignments import get_assignments
from domains.device.services.commands import create_device_command, deliver_command
from domains.notification.enums import AlertSeverity
from domains.notification.services.alerts import record_caregiver_alert
from domains.scheduling.services.occurrences import get_occurrence
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


class NotifyCaregiverHandler:
    action_type = ActionType.NOTIFY_CAREGIVER

    def handle(self, ctx: IntegrationContext, *, payload: dict[str, Any]) -> None:
        dispatch_context = payload.get("dispatch_context") or {}
        occurrence_raw = dispatch_context.get("occurrence_id") or payload.get("occurrence_id")
        if not occurrence_raw:
            return
        occurrence = get_occurrence(uuid.UUID(str(occurrence_raw)))
        activity = get_care_activity_for_schedule(occurrence.schedule_definition_id)
        execution_id = payload.get("workflow_execution_id") or dispatch_context.get("workflow_execution_id")
        record_caregiver_alert(
            elder_id=activity.elder_id,
            title=f"داروی {activity.display_title} هنوز مصرف نشده",
            body="یادآوری روی هاب پاسخ داده نشده است. لطفاً وضعیت سالمند را بررسی کنید.",
            severity=AlertSeverity.ATTENTION,
            source_type="NOTIFY_CAREGIVER",
            source_reference=str(execution_id or occurrence.id),
        )


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
    REGISTRY.register(NotifyCaregiverHandler())
    REGISTRY.register(InitiateCallHandler())
