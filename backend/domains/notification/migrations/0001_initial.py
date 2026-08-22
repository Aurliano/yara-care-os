import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("identity_access", "0002_invitation_role"),
    ]

    operations = [
        migrations.CreateModel(
            name="CaregiverAlert",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=160)),
                ("body", models.CharField(max_length=400)),
                (
                    "severity",
                    models.CharField(
                        choices=[
                            ("urgent", "Urgent"),
                            ("attention", "Attention"),
                            ("reminder", "Reminder"),
                            ("informational", "Informational"),
                        ],
                        max_length=16,
                    ),
                ),
                ("occurred_at", models.DateTimeField()),
                ("source_type", models.CharField(max_length=64)),
                ("source_reference", models.CharField(max_length=128)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                (
                    "elder",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="caregiver_alerts",
                        to="identity_access.elder",
                    ),
                ),
            ],
            options={
                "db_table": "caregiver_alert",
            },
        ),
        migrations.AddIndex(
            model_name="caregiveralert",
            index=models.Index(fields=["elder", "-occurred_at"], name="caregiver_alert_elder_idx"),
        ),
        migrations.AddConstraint(
            model_name="caregiveralert",
            constraint=models.UniqueConstraint(
                fields=("source_type", "source_reference"),
                name="caregiver_alert_source_idempotent",
            ),
        ),
    ]
