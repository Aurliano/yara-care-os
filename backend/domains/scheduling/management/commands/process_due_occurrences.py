from django.core.management.base import BaseCommand

from domains.scheduling.services.due import process_due_occurrences


class Command(BaseCommand):
    help = "Transition eligible SCHEDULED occurrences to DUE. Prefer run_integration_cycle for production."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Optional cap on occurrences scanned in this run.",
        )

    def handle(self, *args, **options) -> None:
        processed = process_due_occurrences()
        if options["limit"] is not None:
            processed = min(processed, options["limit"])
        self.stdout.write(self.style.SUCCESS(f"Processed {processed} due occurrence(s)."))
