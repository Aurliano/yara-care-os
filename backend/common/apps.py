from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "common"
    verbose_name = "Common Infrastructure"

    def ready(self) -> None:
        from common.guards import validate_database_environment

        validate_database_environment()
