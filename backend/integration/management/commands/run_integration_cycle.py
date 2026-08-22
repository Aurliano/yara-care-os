"""Operational integration cycle runner."""

import sys
import time

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
        parser.add_argument(
            "--interval",
            type=int,
            default=None,
            help="Repeat the cycle every N seconds (lab use on Windows without cron).",
        )

    def handle(self, *args, **options) -> None:
        event_limit = options["event_limit"]
        interval = options["interval"]
        if options["dry_run"]:
            suffix = f" every {interval}s" if interval else ""
            self.stdout.write(
                self.style.WARNING(
                    f"Dry run: would execute integration cycle with event_limit={event_limit}{suffix}"
                )
            )
            return

        if interval is not None and interval < 1:
            self.stderr.write(self.style.ERROR("--interval must be a positive number of seconds."))
            sys.exit(1)

        while True:
            ctx = IntegrationContext.new()
            result = run_integration_cycle(ctx, event_limit=event_limit)
            self.stdout.write(self.style.SUCCESS(f"Integration cycle: {result}"))
            if interval is None:
                sys.exit(0)
            try:
                time.sleep(interval)
            except KeyboardInterrupt:
                self.stdout.write("Stopped integration cycle loop.")
                sys.exit(0)
