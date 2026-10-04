from django.apps import AppConfig


class WorkflowConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "domains.workflow"
    label = "workflow"
    verbose_name = "Workflow"

    def ready(self) -> None:
        from domains.workflow.services.scheduling_hooks import register_workflow_scheduling_hooks

        register_workflow_scheduling_hooks()

