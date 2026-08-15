"""Assign a hub device to the dev elder and ensure demo sync payload exists."""

import uuid

from django.core.management.base import BaseCommand, CommandError

from domains.device.enums import AssignmentType
from domains.device.services.assignments import assign_device, get_assignments
from domains.device.enums import AssignmentStatus
from integration.services.hub_dev_seed import ensure_dev_elder_sync_data, get_dev_elder_id


class Command(BaseCommand):
    help = "Seed demo elder sync data and optionally assign a registered hub device."

    def add_arguments(self, parser):
        parser.add_argument(
            "--device-id",
            type=str,
            help="Hub device UUID from Developer Report (assigns device to dev elder).",
        )

    def handle(self, *args, **options):
        elder_id = get_dev_elder_id()
        if elder_id is None:
            raise CommandError("Dev caregiver not found. Run: python manage.py seed_hub_provision")

        ensure_dev_elder_sync_data(elder_id=elder_id)
        self.stdout.write(self.style.SUCCESS(f"Ensured demo sync data for elder {elder_id}."))

        device_id_raw = options.get("device_id")
        if not device_id_raw:
            self.stdout.write("No --device-id provided; skipping hub assignment.")
            return

        device_id = uuid.UUID(device_id_raw)
        active = next(
            (item for item in get_assignments(device_id=device_id) if item.status == AssignmentStatus.ASSIGNED),
            None,
        )
        if active is not None:
            self.stdout.write(f"Device already assigned to elder {active.elder_id}.")
            return

        assign_device(
            device_id=device_id,
            elder_id=elder_id,
            assignment_type=AssignmentType.OWNED,
        )
        self.stdout.write(self.style.SUCCESS(f"Assigned hub {device_id} to dev elder {elder_id}."))
