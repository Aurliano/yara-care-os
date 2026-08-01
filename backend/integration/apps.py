from django.apps import AppConfig


class IntegrationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "integration"
    verbose_name = "Integration Runtime"

    def ready(self) -> None:
        from integration.runtime.action_handlers import register_default_handlers

        register_default_handlers()
