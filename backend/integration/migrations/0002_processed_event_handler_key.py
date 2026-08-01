from django.db import migrations, models


def backfill_handler_names(apps, schema_editor) -> None:
    ProcessedIntegrationEvent = apps.get_model("integration", "ProcessedIntegrationEvent")
    EventRecord = apps.get_model("event", "EventRecord")
    for row in ProcessedIntegrationEvent.objects.all().iterator():
        event = EventRecord.objects.filter(pk=row.event_id).only("event_type").first()
        row.handler_name = event.event_type if event else "unknown"
        row.save(update_fields=["handler_name"])


class Migration(migrations.Migration):

    dependencies = [
        ("event", "0001_initial"),
        ("integration", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="processedintegrationevent",
            name="handler_name",
            field=models.CharField(default="unknown", max_length=128),
            preserve_default=False,
        ),
        migrations.RunPython(backfill_handler_names, migrations.RunPython.noop),
        migrations.RemoveIndex(
            model_name="processedintegrationevent",
            name="integration_evt_consumer_idx",
        ),
        migrations.RemoveField(
            model_name="processedintegrationevent",
            name="consumer",
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE integration_processed_event "
                        "DROP CONSTRAINT integration_processed_event_pkey;"
                        "ALTER TABLE integration_processed_event "
                        "ADD COLUMN id BIGSERIAL PRIMARY KEY;"
                        "ALTER TABLE integration_processed_event "
                        "ADD CONSTRAINT integration_evt_handler_uniq "
                        "UNIQUE (event_id, handler_name);"
                        "CREATE INDEX integration_evt_handler_idx "
                        "ON integration_processed_event (handler_name, processed_at);"
                    ),
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="processedintegrationevent",
                    name="id",
                    field=models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                migrations.AlterField(
                    model_name="processedintegrationevent",
                    name="event_id",
                    field=models.UUIDField(db_index=True),
                ),
                migrations.AddConstraint(
                    model_name="processedintegrationevent",
                    constraint=models.UniqueConstraint(
                        fields=("event_id", "handler_name"),
                        name="integration_evt_handler_uniq",
                    ),
                ),
                migrations.AddIndex(
                    model_name="processedintegrationevent",
                    index=models.Index(
                        fields=["handler_name", "processed_at"],
                        name="integration_evt_handler_idx",
                    ),
                ),
            ],
        ),
    ]
