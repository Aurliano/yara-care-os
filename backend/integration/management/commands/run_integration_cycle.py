"""Operational integration cycle runner."""

import sys
import warnings

from django.core.management.base import BaseCommand

from integration.context import IntegrationContext
from integration.runtime.scheduler import run_integration_cycle


class Command(BaseCommand):
    help = "Run integration cycle: due occurrences, workflow timeouts, and event dispatch."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--event-limit",
            type=int,
            default=100,
            help="Maximum events processed per dispatch batch.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report configured cycle without executing domain side effects.",
        )

    def handle(self, *args, **options) -> None:
        event_limit = options["event_limit"]
        if options["dry_run"]:
            self.stdout.write(
                self.style.WARNING(
                    f"Dry run: would execute integration cycle with event_limit={event_limit}"
                )
            )
            return

        ctx = IntegrationContext.new()
        result = run_integration_cycle(ctx, event_limit=event_limit)
        self.stdout.write(self.style.SUCCESS(f"Integration cycle: {result}"))
        sys.exit(0)
