"""Operational shim delegating OccurrenceDue processing to integration runtime."""

from django.core.management.base import BaseCommand

from integration.context import IntegrationContext
from integration.runtime.scheduler import run_integration_cycle


class Command(BaseCommand):
    help = "Run integration cycle: due occurrences, workflow timeouts, and event dispatch."

    def handle(self, *args, **options):
        ctx = IntegrationContext.new()
        result = run_integration_cycle(ctx)
        self.stdout.write(self.style.SUCCESS(f"Integration cycle: {result}"))
