"""Seed MVP roles and permissions."""

from django.core.management.base import BaseCommand

from domains.identity_access.enums import PermissionCode, RoleCode
from domains.identity_access.models import Permission, Role, RolePermission

ROLE_PERMISSIONS: dict[str, list[str]] = {
    RoleCode.PRIMARY_CAREGIVER: [code.value for code in PermissionCode],
    RoleCode.CAREGIVER: [
        PermissionCode.VIEW_ELDER_STATUS,
        PermissionCode.MANAGE_MEDICATION,
        PermissionCode.MANAGE_CONTACTS,
        PermissionCode.MANAGE_DEVICES,
        PermissionCode.INITIATE_CALL,
    ],
    RoleCode.VIEWER: [PermissionCode.VIEW_ELDER_STATUS],
}

ROLE_NAMES = {
    RoleCode.PRIMARY_CAREGIVER: "Primary Caregiver",
    RoleCode.CAREGIVER: "Caregiver",
    RoleCode.VIEWER: "Viewer",
}


class Command(BaseCommand):
    help = "Seed Identity & Access roles and permissions."

    def handle(self, *args, **options):
        for code in PermissionCode:
            Permission.objects.update_or_create(
                code=code.value,
                defaults={"name": code.label},
            )

        for role_code, permission_codes in ROLE_PERMISSIONS.items():
            role, _ = Role.objects.update_or_create(
                code=role_code.value,
                defaults={"name": ROLE_NAMES[role_code]},
            )
            for permission_code in permission_codes:
                permission = Permission.objects.get(code=permission_code)
                RolePermission.objects.get_or_create(role=role, permission=permission)

        self.stdout.write(self.style.SUCCESS("Identity & Access roles and permissions seeded."))
