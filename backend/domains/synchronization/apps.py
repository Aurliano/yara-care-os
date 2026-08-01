from django.apps import AppConfig


class SynchronizationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "domains.synchronization"
    label = "synchronization"
    verbose_name = "Synchronization"
