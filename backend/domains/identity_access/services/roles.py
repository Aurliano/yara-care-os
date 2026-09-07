"""Role and permission seeding and lookup services."""

from __future__ import annotations

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
        PermissionCode.SEND_MESSAGE,
        PermissionCode.VIEW_MESSAGES,
    ],
    RoleCode.VIEWER: [PermissionCode.VIEW_ELDER_STATUS],
}

ROLE_NAMES: dict[str, str] = {
    RoleCode.PRIMARY_CAREGIVER: "Primary Caregiver",
    RoleCode.CAREGIVER: "Caregiver",
    RoleCode.VIEWER: "Viewer",
}


def seed_baseline_roles_and_permissions() -> None:
    """Seed baseline roles and permissions idempotently."""
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
