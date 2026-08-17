"""Idempotent Family lab seed — distinct from Hub-dev caregiver."""

from __future__ import annotations

import uuid

from django.db import transaction

from domains.communication.enums import CommunicationChannel
from domains.communication.models import Contact
from domains.communication.services.contacts import create_contact, set_priority_contact
from domains.identity_access.enums import MembershipStatus
from domains.identity_access.models import Membership, User
from domains.identity_access.services.profiles import create_elder, create_user
from domains.licensing.services.licenses import (
    activate_license,
    change_license_plan,
    get_active_license_for_elder,
)
from domains.workflow.models import WorkflowDefinition
from domains.workflow.services.executions import create_workflow_definition
from integration.services.hub_dev_seed import DEV_WORKFLOW_CODE, _base_workflow_definition

FAMILY_CAREGIVER_PHONE = "+989121111111"
FAMILY_CAREGIVER_PASSWORD = "familylab123"
FAMILY_CAREGIVER_NAME = "Family Lab Caregiver"
FAMILY_ELDER_NAME = "Family Lab Elder"
FAMILY_CONTACT_NAME = "دختر"


def get_family_lab_elder_id() -> uuid.UUID | None:
    user = User.objects.filter(phone=FAMILY_CAREGIVER_PHONE).first()
    if user is None:
        return None
    membership = (
        Membership.objects.filter(user=user, status=MembershipStatus.ACTIVE)
        .order_by("-is_primary", "-joined_at")
        .first()
    )
    return membership.elder_id if membership else None


def _ensure_medication_workflow() -> WorkflowDefinition:
    workflow = WorkflowDefinition.objects.filter(code=DEV_WORKFLOW_CODE).first()
    if workflow is not None:
        return workflow
    return create_workflow_definition(
        code=DEV_WORKFLOW_CODE,
        name="Hub Dev Medication Reminder",
        definition=_base_workflow_definition(),
    )


def _ensure_premium_license(elder_id: uuid.UUID) -> None:
    existing = get_active_license_for_elder(elder_id)
    if existing is None:
        activate_license(elder_id=elder_id, plan_code="PREMIUM")
        return
    if existing.plan.code != "PREMIUM":
        change_license_plan(license_id=existing.id, plan_code="PREMIUM")


@transaction.atomic
def ensure_family_lab_seed() -> dict[str, str]:
    """Create Family caregiver, licensed elder, VIDEO priority contact, and care workflow."""
    _ensure_medication_workflow()

    user = User.objects.filter(phone=FAMILY_CAREGIVER_PHONE).first()
    created_user = False
    if user is None:
        user = create_user(
            phone=FAMILY_CAREGIVER_PHONE,
            password=FAMILY_CAREGIVER_PASSWORD,
            full_name=FAMILY_CAREGIVER_NAME,
        )
        created_user = True

    elder_id = get_family_lab_elder_id()
    if elder_id is None:
        elder = create_elder(actor=user, full_name=FAMILY_ELDER_NAME)
        elder_id = elder.id
    _ensure_premium_license(elder_id)

    contact = Contact.objects.filter(elder_id=elder_id, display_name=FAMILY_CONTACT_NAME).first()
    if contact is None:
        contact = create_contact(
            elder_id=elder_id,
            display_name=FAMILY_CONTACT_NAME,
            phone=FAMILY_CAREGIVER_PHONE,
            preferred_channel=CommunicationChannel.VIDEO,
            communication_identities=[{"type": "phone", "value": FAMILY_CAREGIVER_PHONE}],
        )
    elif contact.preferred_channel != CommunicationChannel.VIDEO:
        contact.preferred_channel = CommunicationChannel.VIDEO
        contact.save(update_fields=["preferred_channel", "updated_at"])
    if not contact.is_priority:
        set_priority_contact(contact_id=contact.id)

    return {
        "phone": FAMILY_CAREGIVER_PHONE,
        "password": FAMILY_CAREGIVER_PASSWORD,
        "elder_id": str(elder_id),
        "user_created": str(created_user).lower(),
        "contact_id": str(contact.id),
    }
