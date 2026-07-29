from django.apps import AppConfig


class EventConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "domains.event"
    label = "event"
    verbose_name = "Event"
