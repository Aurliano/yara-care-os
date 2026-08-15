"""Seed default hub device model and dev caregiver for tablet provisioning."""

from django.core.management.base import BaseCommand

from domains.device.enums import DeviceCapabilityCode
from domains.device.services.device_models import register_device_model
from domains.identity_access.models import User
from domains.identity_access.services.profiles import create_elder, create_user
from domains.licensing.services.licenses import activate_license

from integration.services.hub_dev_seed import (
    DEV_CAREGIVER_PASSWORD,
    DEV_CAREGIVER_PHONE,
    ensure_dev_elder_sync_data,
    get_dev_elder_id,
)


class Command(BaseCommand):
    help = "Seed YARA-HUB-TABLET model, dev caregiver, and demo sync payload."

    def handle(self, *args, **options):
        register_device_model(
            manufacturer="Yara",
            model_code="YARA-HUB-TABLET",
            model_name="Yara Hub Tablet",
            capability_codes=[
                DeviceCapabilityCode.DISPLAY,
                DeviceCapabilityCode.SPEAKER,
                DeviceCapabilityCode.BLE,
                DeviceCapabilityCode.BATTERY,
            ],
            device_type="HUB",
        )
        self.stdout.write(self.style.SUCCESS("Seeded YARA-HUB-TABLET device model."))

        user = User.objects.filter(phone=DEV_CAREGIVER_PHONE).first()
        if user is None:
            user = create_user(
                phone=DEV_CAREGIVER_PHONE,
                password=DEV_CAREGIVER_PASSWORD,
                full_name="Hub Dev Caregiver",
            )
            elder = create_elder(actor=user, full_name="Hub Dev Elder")
            activate_license(elder_id=elder.id, plan_code="BASIC")
            self.stdout.write(
                self.style.SUCCESS(
                    f"Seeded dev caregiver {DEV_CAREGIVER_PHONE} with licensed elder {elder.id}."
                )
            )
        else:
            elder_id = get_dev_elder_id()
            if elder_id is None:
                elder = create_elder(actor=user, full_name="Hub Dev Elder")
                activate_license(elder_id=elder.id, plan_code="BASIC")
                elder_id = elder.id
                self.stdout.write(self.style.SUCCESS(f"Created licensed elder {elder_id} for dev caregiver."))
            else:
                self.stdout.write(f"Dev caregiver {DEV_CAREGIVER_PHONE} already exists.")

        elder_id = get_dev_elder_id()
        if elder_id is not None:
            ensure_dev_elder_sync_data(elder_id=elder_id)
            self.stdout.write(self.style.SUCCESS("Ensured demo care/workflow/contact sync data."))
