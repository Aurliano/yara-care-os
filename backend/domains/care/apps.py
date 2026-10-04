from django.apps import AppConfig


class CareConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "domains.care"
    label = "care"
    verbose_name = "Care"

    def ready(self) -> None:
        import domains.care.signals  # noqa: F401
        from domains.care.services.authorizers import register_care_authorizers

        register_care_authorizers()


