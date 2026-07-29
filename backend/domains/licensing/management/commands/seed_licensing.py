"""Seed MVP plans and entitlements."""

from django.core.management.base import BaseCommand

from domains.licensing.enums import EntitlementKey, EntitlementKind
from domains.licensing.services.plans import configure_plan_entitlement, create_plan


PLAN_DEFINITIONS = {
    "BASIC": {
        "name": "Basic",
        "entitlements": {
            EntitlementKey.MAX_CAREGIVERS: ("2", EntitlementKind.LIMIT),
            EntitlementKey.MAX_HUBS: ("1", EntitlementKind.LIMIT),
            EntitlementKey.MAX_PILLBOXES: ("1", EntitlementKind.LIMIT),
            EntitlementKey.PILLBOX_SUPPORT: ("enabled", EntitlementKind.FEATURE),
            EntitlementKey.SENSOR_SUPPORT: ("disabled", EntitlementKind.FEATURE),
            EntitlementKey.VIDEO_CALL: ("disabled", EntitlementKind.FEATURE),
        },
    },
    "PLUS": {
        "name": "Plus",
        "entitlements": {
            EntitlementKey.MAX_CAREGIVERS: ("5", EntitlementKind.LIMIT),
            EntitlementKey.MAX_HUBS: ("1", EntitlementKind.LIMIT),
            EntitlementKey.MAX_PILLBOXES: ("1", EntitlementKind.LIMIT),
            EntitlementKey.PILLBOX_SUPPORT: ("enabled", EntitlementKind.FEATURE),
            EntitlementKey.SENSOR_SUPPORT: ("enabled", EntitlementKind.FEATURE),
            EntitlementKey.VIDEO_CALL: ("disabled", EntitlementKind.FEATURE),
        },
    },
    "PREMIUM": {
        "name": "Premium",
        "entitlements": {
            EntitlementKey.MAX_CAREGIVERS: ("10", EntitlementKind.LIMIT),
            EntitlementKey.MAX_HUBS: ("1", EntitlementKind.LIMIT),
            EntitlementKey.MAX_PILLBOXES: ("2", EntitlementKind.LIMIT),
            EntitlementKey.PILLBOX_SUPPORT: ("enabled", EntitlementKind.FEATURE),
            EntitlementKey.SENSOR_SUPPORT: ("enabled", EntitlementKind.FEATURE),
            EntitlementKey.VIDEO_CALL: ("enabled", EntitlementKind.FEATURE),
        },
    },
}


class Command(BaseCommand):
    help = "Seed Licensing plans and entitlements."

    def handle(self, *args, **options):
        for code, definition in PLAN_DEFINITIONS.items():
            from domains.licensing.models import Plan

            plan, _ = Plan.objects.get_or_create(
                code=code,
                defaults={"name": definition["name"]},
            )
            if plan.name != definition["name"]:
                plan.name = definition["name"]
                plan.save(update_fields=["name"])

            for entitlement_key, (value, kind) in definition["entitlements"].items():
                configure_plan_entitlement(
                    plan=plan,
                    entitlement_key=entitlement_key.value,
                    kind=kind,
                    value=value,
                    description=entitlement_key.label,
                )

        self.stdout.write(self.style.SUCCESS("Licensing plans and entitlements seeded."))
