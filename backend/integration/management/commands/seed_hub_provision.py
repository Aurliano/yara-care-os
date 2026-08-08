"""Seed default hub device model for provisioning."""

from django.core.management.base import BaseCommand

from domains.device.enums import DeviceCapabilityCode
from domains.device.services.device_models import register_device_model


class Command(BaseCommand):
    help = "Seed default YARA hub tablet device model for hub provisioning."

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
