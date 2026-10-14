# Generated for Device domain baseline tablet model seeding

from django.db import migrations

CAPABILITIES = [
    ("DISPLAY", "Display"),
    ("SPEAKER", "Speaker"),
    ("MICROPHONE", "Microphone"),
    ("CAMERA", "Camera"),
    ("BLE", "Ble"),
    ("BATTERY", "Battery"),
]


def seed_yara_hub_tablet_model(apps, schema_editor):
    DeviceModel = apps.get_model("device", "DeviceModel")
    DeviceCapability = apps.get_model("device", "DeviceCapability")
    DeviceModelCapability = apps.get_model("device", "DeviceModelCapability")

    model, _ = DeviceModel.objects.update_or_create(
        model_code="YARA-HUB-TABLET",
        defaults={
            "manufacturer": "Yara",
            "model_name": "Yara Hub Tablet",
            "device_type": "HUB",
            "status": "ACTIVE",
        },
    )

    for code, name in CAPABILITIES:
        cap, _ = DeviceCapability.objects.update_or_create(
            code=code,
            defaults={"name": name},
        )
        DeviceModelCapability.objects.get_or_create(
            device_model=model,
            capability=cap,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("device", "0002_device_aggregate_version"),
    ]

    operations = [
        migrations.RunPython(seed_yara_hub_tablet_model, migrations.RunPython.noop),
    ]
