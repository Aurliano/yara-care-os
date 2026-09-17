"""Dev/Test-only management command to safely remove exactly one target Device.

Used specifically for simulating stale-device recovery scenarios (e.g. Scenario P1).
Enforces strict environment, database, and confirmation safeguards.
"""

from __future__ import annotations

import uuid
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q

from domains.device.enums import AssignmentStatus
from domains.device.models import (
    Compartment,
    CompartmentAssignment,
    Device,
    DeviceAssignment,
    DeviceCapabilityOverride,
    DeviceCommand,
    Pairing,
)
from integration.services.hub_provisioning import PROVISIONING_CONFIG_KEY


class Command(BaseCommand):
    help = "Safely remove exactly one test Device and its direct device-domain relations."

    def add_arguments(self, parser):
        parser.add_argument(
            "--device-id",
            type=str,
            required=True,
            help="UUID of the device to remove.",
        )
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Explicit confirmation required to execute deletion. Without this flag, dry-run is performed.",
        )

    def handle(self, *args, **options):
        # 1. Strict environment & database safeguards
        if not settings.DEBUG:
            raise CommandError(
                "CRITICAL SAFETY CHECK FAILED: Refusing to execute because DEBUG is False. "
                "This command cannot run against production environments."
            )

        db_name = str(settings.DATABASES.get("default", {}).get("NAME", "")).lower()
        if "prod" in db_name or "production" in db_name:
            raise CommandError(
                f"CRITICAL SAFETY CHECK FAILED: Database name '{db_name}' appears to be production. Aborting."
            )

        # 2. Parse target device UUID
        raw_device_id = options.get("device_id")
        try:
            device_uuid = uuid.UUID(raw_device_id)
        except (ValueError, TypeError) as exc:
            raise CommandError(f"Invalid device UUID: '{raw_device_id}'") from exc

        # 3. Authoritative lookup
        device = Device.objects.filter(id=device_uuid).select_related("device_model").first()
        if device is None:
            raise CommandError(f"Target device with ID '{device_uuid}' does not exist in backend.")

        # 4. Extract device and provisioning metadata
        config: dict[str, Any] = device.configuration or {}
        prov_blob: dict[str, Any] = config.get(PROVISIONING_CONFIG_KEY, {})
        replica_identifier = prov_blob.get("replica_identifier")
        prov_state = prov_blob.get("provisioning_state", "UNKNOWN")
        download_scope = prov_blob.get("download_scope_elder_id")

        active_assignment = (
            DeviceAssignment.objects.filter(device=device, status=AssignmentStatus.ASSIGNED)
            .select_related("elder")
            .first()
        )
        assigned_elder_str = (
            f"{active_assignment.elder.full_name} ({active_assignment.elder.id})"
            if active_assignment and active_assignment.elder
            else "None"
        )

        all_assignments_count = DeviceAssignment.objects.filter(device=device).count()
        commands_count = DeviceCommand.objects.filter(target_device=device).count()
        pairings_count = Pairing.objects.filter(Q(hub_device=device) | Q(peripheral_device=device)).count()
        compartments_count = Compartment.objects.filter(device=device).count()
        overrides_count = DeviceCapabilityOverride.objects.filter(device=device).count()

        # 5. Print target before deletion
        self.stdout.write(self.style.NOTICE("=================================================="))
        self.stdout.write(self.style.NOTICE("TARGET DEVICE DETAILS"))
        self.stdout.write(self.style.NOTICE("=================================================="))
        self.stdout.write(f"Device ID:               {device.id}")
        self.stdout.write(f"Serial Number:           {device.serial_number}")
        self.stdout.write(f"Device Model:            {device.device_model.model_code}")
        self.stdout.write(f"Operational Status:      {device.operational_status}")
        self.stdout.write(f"Provisioning State:      {prov_state}")
        self.stdout.write(f"Replica Identifier:      {replica_identifier}")
        self.stdout.write(f"Download Scope Elder:    {download_scope}")
        self.stdout.write(f"Active Assigned Elder:   {assigned_elder_str}")
        self.stdout.write(f"Total Assignment Records:{all_assignments_count}")
        self.stdout.write(f"Direct Commands:         {commands_count}")
        self.stdout.write(f"Direct Pairings:         {pairings_count}")
        self.stdout.write(f"Direct Compartments:     {compartments_count}")
        self.stdout.write(f"Capability Overrides:    {overrides_count}")
        self.stdout.write(self.style.NOTICE("=================================================="))

        # 6. Check confirmation flag
        if not options.get("confirm"):
            self.stdout.write(
                self.style.WARNING(
                    "\n[DRY-RUN] Confirmation flag --confirm was not specified. No records were deleted.\n"
                    f"To execute deletion of this device, run:\n"
                    f"  python manage.py remove_test_device --device-id {device.id} --confirm\n"
                )
            )
            return

        # 7. Execute scoped atomic deletion
        self.stdout.write(self.style.WARNING("\nExecuting scoped deletion of target device..."))

        with transaction.atomic():
            del_commands = DeviceCommand.objects.filter(target_device=device).delete()[0]
            del_comp_assignments = CompartmentAssignment.objects.filter(compartment__device=device).delete()[0]
            del_compartments = Compartment.objects.filter(device=device).delete()[0]
            del_pairings = Pairing.objects.filter(Q(hub_device=device) | Q(peripheral_device=device)).delete()[0]
            del_overrides = DeviceCapabilityOverride.objects.filter(device=device).delete()[0]
            del_assignments = DeviceAssignment.objects.filter(device=device).delete()[0]
            del_device = device.delete()[0]

        # 8. Verify post-conditions
        exists_after = Device.objects.filter(id=device_uuid).exists()
        if exists_after:
            raise CommandError(f"Deletion failed: Device '{device_uuid}' still exists in database.")

        self.stdout.write(self.style.SUCCESS("\nDEVICE SUCCESSFULLY REMOVED"))
        self.stdout.write(f"Deleted Device records:                {del_device}")
        self.stdout.write(f"Deleted DeviceAssignment records:      {del_assignments}")
        self.stdout.write(f"Deleted DeviceCommand records:         {del_commands}")
        self.stdout.write(f"Deleted Pairing records:               {del_pairings}")
        self.stdout.write(f"Deleted Compartment records:           {del_compartments}")
        self.stdout.write(f"Deleted CompartmentAssignment records: {del_comp_assignments}")
        self.stdout.write(f"Deleted CapabilityOverride records:    {del_overrides}")
        self.stdout.write(self.style.SUCCESS("All unrelated models, Elders, and sync history preserved."))
