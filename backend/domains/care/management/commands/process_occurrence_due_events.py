"""
Deprecated operational shim.

Use ``python manage.py run_integration_cycle`` instead.
"""

import warnings

from django.core.management.base import BaseCommand

from domains.care.services.occurrence_due import handle_occurrence_due_event
from domains.event.models import EventRecord


class Command(BaseCommand):
    help = "Deprecated: use run_integration_cycle."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options) -> None:
        warnings.warn(
            "process_occurrence_due_events is deprecated; use run_integration_cycle.",
            DeprecationWarning,
            stacklevel=2,
        )
        limit = options["limit"]
        events = EventRecord.objects.filter(event_type="OccurrenceDue").order_by("recorded_at")[:limit]
        processed = 0
        for event in events:
            handle_occurrence_due_event(event_id=event.id)
            processed += 1
        self.stdout.write(self.style.WARNING(f"Deprecated command processed {processed} OccurrenceDue event(s)."))
