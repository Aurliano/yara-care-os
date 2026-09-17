"""Management command to reset development/test data and establish a clean baseline."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from domains.billing.models import Invoice, InvoiceLineItem, PaymentAttempt
from domains.care.enums import CareActivityType
from domains.care.models import CareActivity, CareCompletion, Prescription
from domains.care.services.prescriptions import create_prescription
from domains.communication.enums import CommunicationChannel
from domains.communication.models import (
    CallAttempt,
    CommunicationSession,
    Contact,
    Message,
    MessageAttachment,
    MessageRecipient,
    SessionParticipant,
)
from domains.communication.services.contacts import create_contact, set_priority_contact
from domains.device.enums import DeviceCapabilityCode
from domains.device.models import (
    Compartment,
    CompartmentAssignment,
    Device,
    DeviceAssignment,
    DeviceCapabilityOverride,
    DeviceCommand,
    Pairing,
)
from domains.device.services.device_models import register_device_model
from domains.event.models import EventOutbox, EventRecord
from domains.identity_access.models import (
    Elder,
    EmergencyRecipient,
    Invitation,
    Membership,
    User,
)
from domains.identity_access.services.profiles import create_elder, create_user
from domains.identity_access.services.roles import seed_baseline_roles_and_permissions
from domains.licensing.models import License, LicensePlanHistory, Subscription
from domains.licensing.services.licenses import activate_license
from domains.notification.models import CaregiverAlert
from domains.scheduling.models import Occurrence, ScheduleDefinition, ScheduleException
from domains.synchronization.models import (
    ReplicaState,
    ReplicaVersion,
    SynchronizationConflict,
    SynchronizationOperation,
    SynchronizationSession,
)
from domains.workflow.medication_reminder_policy import medication_reminder_definition
from domains.workflow.models import ActionResult, ConfirmationEvidence, WorkflowDefinition, WorkflowExecution
from domains.workflow.services.executions import create_workflow_definition
from infrastructure.models import (
    ProviderCallBinding,
    ProviderRoomBinding,
    ProviderUserBinding,
)
from integration.models import ProcessedIntegrationEvent

SEED_CAREGIVER_PHONE = "+989121111111"
SEED_CAREGIVER_PASSWORD = "familylab123"
SEED_CAREGIVER_NAME = "Family Lab Caregiver"
SEED_ELDER_NAME = "Family Lab Elder"
SEED_CONTACT_NAME = "دختر"
SEED_WORKFLOW_CODE = "wf-hub-dev-medication"
SEED_ACTIVITY_TITLE = "Morning Medication"


class Command(BaseCommand):
    help = "Safely reset test data and establish clean deterministic baseline for MVP QA."

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Explicit confirmation required to execute reset.",
        )

    def handle(self, *args, **options):
        # 1. Strict production safety checks
        if not settings.DEBUG:
            raise CommandError(
                "CRITICAL SAFETY CHECK FAILED: Refusing to reset test environment because DEBUG is False. "
                "This command cannot run against production environments."
            )

        db_name = str(settings.DATABASES.get("default", {}).get("NAME", "")).lower()
        if "prod" in db_name or "production" in db_name:
            raise CommandError(
                f"CRITICAL SAFETY CHECK FAILED: Database name '{db_name}' appears to be production. Aborting."
            )

        if not options.get("confirm"):
            raise CommandError(
                "Confirmation flag --confirm is required. "
                "Usage: python manage.py reset_test_environment --confirm"
            )

        self.stdout.write(self.style.WARNING("Initiating clean environment reset..."))

        # 2. Deletion in strict reverse foreign-key dependency order
        with transaction.atomic():
            # Infrastructure bindings
            ProviderCallBinding.objects.all().delete()
            ProviderRoomBinding.objects.all().delete()
            ProviderUserBinding.objects.all().delete()

            # Communication
            MessageRecipient.objects.all().delete()
            MessageAttachment.objects.all().delete()
            Message.objects.all().delete()
            CallAttempt.objects.all().delete()
            SessionParticipant.objects.all().delete()
            CommunicationSession.objects.all().delete()
            Contact.objects.all().delete()

            # Care
            CareCompletion.objects.all().delete()
            Prescription.objects.all().delete()
            CareActivity.objects.all().delete()

            # Workflow
            ActionResult.objects.all().delete()
            ConfirmationEvidence.objects.all().delete()
            WorkflowExecution.objects.all().delete()

            # Scheduling
            ScheduleException.objects.all().delete()
            Occurrence.objects.all().delete()
            ScheduleDefinition.objects.all().delete()

            # Device
            DeviceCommand.objects.all().delete()
            CompartmentAssignment.objects.all().delete()
            Compartment.objects.all().delete()
            Pairing.objects.all().delete()
            DeviceCapabilityOverride.objects.all().delete()
            DeviceAssignment.objects.all().delete()
            Device.objects.all().delete()

            # Synchronization
            SynchronizationOperation.objects.all().delete()
            SynchronizationConflict.objects.all().delete()
            ReplicaVersion.objects.all().delete()
            SynchronizationSession.objects.all().delete()
            ReplicaState.objects.all().delete()

            # Notifications & Integration
            CaregiverAlert.objects.all().delete()
            ProcessedIntegrationEvent.objects.all().delete()

            # Events
            EventOutbox.objects.all().delete()
            EventRecord.objects.all().delete()

            # Billing & Licensing transactions
            PaymentAttempt.objects.all().delete()
            InvoiceLineItem.objects.all().delete()
            Invoice.objects.all().delete()
            Subscription.objects.all().delete()
            LicensePlanHistory.objects.all().delete()
            License.objects.all().delete()

            # Identity relationships & test entities
            EmergencyRecipient.objects.all().delete()
            Invitation.objects.all().delete()
            Membership.objects.all().delete()
            Elder.objects.all().delete()
            User.objects.all().delete()

            self.stdout.write(self.style.SUCCESS("Purged disposable test data successfully."))

            # 3. Seed Production Baseline Configurations
            seed_baseline_roles_and_permissions()
            call_command("seed_licensing", stdout=self.stdout)
            call_command("seed_billing", stdout=self.stdout)

            register_device_model(
                manufacturer="Yara",
                model_code="YARA-HUB-TABLET",
                model_name="Yara Hub Tablet",
                capability_codes=[
                    DeviceCapabilityCode.DISPLAY,
                    DeviceCapabilityCode.SPEAKER,
                    DeviceCapabilityCode.MICROPHONE,
                    DeviceCapabilityCode.CAMERA,
                    DeviceCapabilityCode.BLE,
                    DeviceCapabilityCode.BATTERY,
                ],
                device_type="HUB",
            )

            workflow = WorkflowDefinition.objects.filter(code=SEED_WORKFLOW_CODE).first()
            if workflow is None:
                workflow = create_workflow_definition(
                    code=SEED_WORKFLOW_CODE,
                    name="Hub Dev Medication Reminder",
                    definition=medication_reminder_definition(),
                )

            # 4. Seed Minimal Deterministic Baseline
            caregiver = create_user(
                phone=SEED_CAREGIVER_PHONE,
                password=SEED_CAREGIVER_PASSWORD,
                full_name=SEED_CAREGIVER_NAME,
            )
            elder = create_elder(actor=caregiver, full_name=SEED_ELDER_NAME)
            activate_license(elder_id=elder.id, plan_code="PREMIUM")

            contact = create_contact(
                elder_id=elder.id,
                display_name=SEED_CONTACT_NAME,
                phone=SEED_CAREGIVER_PHONE,
                preferred_channel=CommunicationChannel.VIDEO,
                communication_identities=[{"type": "phone", "value": SEED_CAREGIVER_PHONE}],
            )
            set_priority_contact(contact_id=contact.id)

            create_prescription(
                elder_id=elder.id,
                workflow_definition_id=workflow.id,
                recurrence_definition={"type": "daily", "time": "08:00"},
                timezone_name="Asia/Tehran",
                start_at=datetime(2026, 1, 1, 0, 0, tzinfo=ZoneInfo("UTC")),
                display_title=SEED_ACTIVITY_TITLE,
                display_subtitle="Take with water",
                medication_reference="med-aspirin-81",
                dosage_information="1 قرص با آب",
                elder_friendly_description="قرص آسپرین برای قلب",
                personalized_description="مصرف بعد از صبحانه",
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n=== CLEAN BASELINE ESTABLISHED ===\n"
                f"Caregiver Phone: {SEED_CAREGIVER_PHONE}\n"
                f"Caregiver Password: {SEED_CAREGIVER_PASSWORD}\n"
                f"Elder ID: {elder.id}\n"
                f"Elder Name: {SEED_ELDER_NAME}\n"
                f"Plan: PREMIUM\n"
                f"Priority Contact: Daughter (VIDEO)\n"
                f"Care Activity: {SEED_ACTIVITY_TITLE} (Daily 08:00 Asia/Tehran)\n"
                f"Prescription: Aspirin (med-aspirin-81)\n"
                f"Hub Device Model: YARA-HUB-TABLET\n"
                f"Server ready for clean Hub provisioning.\n"
            )
        )
