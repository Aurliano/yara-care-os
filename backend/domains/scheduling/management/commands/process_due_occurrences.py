from django.core.management.base import BaseCommand

from domains.scheduling.services.due import process_due_occurrences


class Command(BaseCommand):
    help = "Transition eligible SCHEDULED occurrences to DUE."

    def handle(self, *args, **options):
        processed = process_due_occurrences()
        self.stdout.write(self.style.SUCCESS(f"Processed {processed} due occurrence(s)."))
