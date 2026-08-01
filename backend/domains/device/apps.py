from django.apps import AppConfig


class DeviceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "domains.device"
    label = "device"
    verbose_name = "Device"
