"""Family lab seed is distinct from Hub-dev and grants PREMIUM video."""

import uuid

import pytest

from domains.communication.enums import CommunicationChannel
from domains.communication.models import Contact
from domains.device.enums import DeviceCapabilityCode
from domains.device.models import DeviceModel
from domains.identity_access.models import User
from domains.licensing.enums import EntitlementKey
from domains.licensing.services.entitlements import can_use_feature
from domains.workflow.models import WorkflowDefinition
from integration.services.family_lab_seed import (
    FAMILY_CAREGIVER_PHONE,
    FAMILY_CONTACT_NAME,
    ensure_family_lab_seed,
)
from integration.services.hub_dev_seed import DEV_CAREGIVER_PHONE, DEV_WORKFLOW_CODE


@pytest.mark.django_db
def test_seed_family_lab_is_idempotent_premium_video_contact():
    first = ensure_family_lab_seed()
    second = ensure_family_lab_seed()

    assert first["phone"] == FAMILY_CAREGIVER_PHONE
    assert first["elder_id"] == second["elder_id"]
    assert first["contact_id"] == second["contact_id"]
    assert first["phone"] != DEV_CAREGIVER_PHONE
    assert User.objects.filter(phone=FAMILY_CAREGIVER_PHONE).exists()

    elder_id = uuid.UUID(first["elder_id"])
    assert can_use_feature(elder_id, EntitlementKey.VIDEO_CALL) is True

    contact = Contact.objects.get(pk=first["contact_id"])
    assert contact.display_name == FAMILY_CONTACT_NAME
    assert contact.preferred_channel == CommunicationChannel.VIDEO
    assert contact.is_priority is True
    assert WorkflowDefinition.objects.filter(code=DEV_WORKFLOW_CODE).exists()


@pytest.mark.django_db
def test_seed_hub_provision_adds_camera_and_microphone():
    from django.core.management import call_command

    call_command("seed_hub_provision", verbosity=0)
    model = DeviceModel.objects.get(model_code="YARA-HUB-TABLET")
    codes = set(model.model_capabilities.values_list("capability__code", flat=True))
    assert DeviceCapabilityCode.CAMERA in codes
    assert DeviceCapabilityCode.MICROPHONE in codes
