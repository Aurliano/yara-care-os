"""
Deprecated operational shim.

Use ``python manage.py run_integration_cycle`` instead, which processes due
occurrences, workflow timeouts, and integration event dispatch in one cycle.
"""
from django.core.management.base import BaseCommand

from domains.care.services.occurrence_due import handle_occurrence_due_event
from domains.event.models import EventRecord


class Command(BaseCommand):
    help = "Process OccurrenceDue events by resolving CareActivity and starting Workflow execution."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options) -> None:
        limit = options["limit"]
        events = EventRecord.objects.filter(event_type="OccurrenceDue").order_by("recorded_at")[:limit]
        processed = 0
        for event in events:
            handle_occurrence_due_event(event_id=event.id)
            processed += 1
        self.stdout.write(self.style.SUCCESS(f"Processed {processed} OccurrenceDue event(s)."))
