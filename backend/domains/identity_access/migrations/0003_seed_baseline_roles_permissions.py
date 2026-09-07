# Generated for Identity & Access baseline roles and permissions seeding

from django.db import migrations


PERMISSIONS_DATA = [
    ("VIEW_ELDER_STATUS", "View Elder Status"),
    ("MANAGE_MEDICATION", "Manage Medication"),
    ("MANAGE_CONTACTS", "Manage Contacts"),
    ("MANAGE_DEVICES", "Manage Devices"),
    ("INITIATE_CALL", "Initiate Call"),
    ("MANAGE_MEMBERS", "Manage Members"),
    ("MANAGE_SUBSCRIPTION", "Manage Subscription"),
    ("SEND_MESSAGE", "Send Message"),
    ("VIEW_MESSAGES", "View Messages"),
]

ROLES_DATA = [
    ("PRIMARY_CAREGIVER", "Primary Caregiver"),
    ("CAREGIVER", "Caregiver"),
    ("VIEWER", "Viewer"),
]

ROLE_PERMISSIONS_MAPPING = {
    "PRIMARY_CAREGIVER": [code for code, _ in PERMISSIONS_DATA],
    "CAREGIVER": [
        "VIEW_ELDER_STATUS",
        "MANAGE_MEDICATION",
        "MANAGE_CONTACTS",
        "MANAGE_DEVICES",
        "INITIATE_CALL",
        "SEND_MESSAGE",
        "VIEW_MESSAGES",
    ],
    "VIEWER": [
        "VIEW_ELDER_STATUS",
    ],
}


def seed_baseline_roles_and_permissions(apps, schema_editor):
    Permission = apps.get_model("identity_access", "Permission")
    Role = apps.get_model("identity_access", "Role")
    RolePermission = apps.get_model("identity_access", "RolePermission")

    permissions_by_code = {}
    for code, name in PERMISSIONS_DATA:
        perm, _ = Permission.objects.update_or_create(
            code=code,
            defaults={"name": name},
        )
        permissions_by_code[code] = perm

    for role_code, role_name in ROLES_DATA:
        role, _ = Role.objects.update_or_create(
            code=role_code,
            defaults={"name": role_name},
        )
        for perm_code in ROLE_PERMISSIONS_MAPPING.get(role_code, []):
            perm = permissions_by_code.get(perm_code)
            if perm:
                RolePermission.objects.get_or_create(role=role, permission=perm)


class Migration(migrations.Migration):

    dependencies = [
        ("identity_access", "0002_invitation_role"),
    ]

    operations = [
        migrations.RunPython(seed_baseline_roles_and_permissions, migrations.RunPython.noop),
    ]
