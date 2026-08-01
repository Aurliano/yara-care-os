from django.core.management.base import BaseCommand

from domains.workflow.services.timeout import process_workflow_timeouts


class Command(BaseCommand):
    help = "Process timed-out ACTIVE workflow executions. Prefer run_integration_cycle for production."

    def handle(self, *args, **options) -> None:
        processed = process_workflow_timeouts()
        self.stdout.write(self.style.SUCCESS(f"Processed {processed} timed-out execution(s)."))
