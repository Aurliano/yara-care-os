# Generated for Contract V1.1 — Invitation.role_id

import django.db.models.deletion
from django.db import migrations, models


def backfill_invitation_roles(apps, schema_editor):
    Invitation = apps.get_model("identity_access", "Invitation")
    Role = apps.get_model("identity_access", "Role")

    if not Invitation.objects.filter(role__isnull=True).exists():
        return

    viewer, _ = Role.objects.get_or_create(
        code="VIEWER",
        defaults={"name": "Viewer"},
    )
    Invitation.objects.filter(role__isnull=True).update(role=viewer)


class Migration(migrations.Migration):

    dependencies = [
        ("identity_access", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="invitation",
            name="role",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="invitations",
                to="identity_access.role",
            ),
        ),
        migrations.RunPython(backfill_invitation_roles, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="invitation",
            name="role",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="invitations",
                to="identity_access.role",
            ),
        ),
    ]
