"""Seed MVP roles and permissions."""

from django.core.management.base import BaseCommand

from domains.identity_access.services.roles import seed_baseline_roles_and_permissions


class Command(BaseCommand):
    help = "Seed Identity & Access roles and permissions."

    def handle(self, *args, **options):
        seed_baseline_roles_and_permissions()
        self.stdout.write(self.style.SUCCESS("Identity & Access roles and permissions seeded."))
