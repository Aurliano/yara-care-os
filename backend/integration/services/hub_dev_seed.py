"""Idempotent dev sync payload for hub tablet testing."""

from __future__ import annotations

import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from django.db import transaction

from domains.care.enums import CareActivityType
from domains.care.models import CareActivity
from domains.care.services.activities import create_care_activity
from domains.communication.enums import CommunicationChannel
from domains.communication.models import Contact
from domains.communication.services.contacts import create_contact
from domains.identity_access.enums import MembershipStatus
from domains.identity_access.models import Elder, Membership, User
from domains.workflow.medication_reminder_policy import medication_reminder_definition
from domains.workflow.models import WorkflowDefinition
from domains.workflow.services.executions import create_workflow_definition

DEV_CAREGIVER_PHONE = "+989136666666"
DEV_CAREGIVER_PASSWORD = "securepass123"
DEV_WORKFLOW_CODE = "wf-hub-dev-medication"
DEV_ACTIVITY_TITLE = "Morning Medication"
DEV_CONTACT_NAME = "Dev Caregiver Contact"


def _base_workflow_definition() -> dict:
    return medication_reminder_definition()


def get_dev_elder_id() -> uuid.UUID | None:
    user = User.objects.filter(phone=DEV_CAREGIVER_PHONE).first()
    if user is None:
        return None
    membership = (
        Membership.objects.filter(user=user, status=MembershipStatus.ACTIVE)
        .order_by("-is_primary", "-joined_at")
        .first()
    )
    return membership.elder_id if membership else None


@transaction.atomic
def ensure_dev_elder_sync_data(*, elder_id: uuid.UUID) -> None:
    """Ensure demo care, workflow, and contact data exist for hub snapshot staging."""
    Elder.objects.get(pk=elder_id)

    workflow = WorkflowDefinition.objects.filter(code=DEV_WORKFLOW_CODE).first()
    if workflow is None:
        workflow = create_workflow_definition(
            code=DEV_WORKFLOW_CODE,
            name="Hub Dev Medication Reminder",
            definition=_base_workflow_definition(),
        )

    if not CareActivity.objects.filter(elder_id=elder_id, display_title=DEV_ACTIVITY_TITLE).exists():
        create_care_activity(
            elder_id=elder_id,
            activity_type=CareActivityType.MEDICATION,
            workflow_definition_id=workflow.id,
            recurrence_definition={"type": "daily", "time": "08:00"},
            timezone_name="Asia/Tehran",
            start_at=datetime(2026, 1, 1, 0, 0, tzinfo=ZoneInfo("UTC")),
            display_title=DEV_ACTIVITY_TITLE,
            display_subtitle="Take with water",
        )

    if not Contact.objects.filter(elder_id=elder_id, display_name=DEV_CONTACT_NAME).exists():
        create_contact(
            elder_id=elder_id,
            display_name=DEV_CONTACT_NAME,
            phone=DEV_CAREGIVER_PHONE,
            preferred_channel=CommunicationChannel.VOICE,
            communication_identities=[{"type": "phone", "value": DEV_CAREGIVER_PHONE}],
        )
