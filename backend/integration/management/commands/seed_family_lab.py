"""Seed a Family caregiver lab account distinct from Hub-dev."""

from django.core.management.base import BaseCommand

from integration.services.family_lab_seed import (
    FAMILY_CAREGIVER_PASSWORD,
    FAMILY_CAREGIVER_PHONE,
    ensure_family_lab_seed,
)


class Command(BaseCommand):
    help = "Seed Family lab caregiver, PREMIUM elder, VIDEO priority contact, and medication workflow."

    def handle(self, *args, **options):
        result = ensure_family_lab_seed()
        self.stdout.write(
            self.style.SUCCESS(
                "Family lab ready. "
                f"Login {FAMILY_CAREGIVER_PHONE} / {FAMILY_CAREGIVER_PASSWORD}. "
                f"Elder {result['elder_id']}. "
                "Hub local.properties: hub.provision.phone/password for this caregiver."
            )
        )
