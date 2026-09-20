import os
import sys
import django

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.db.models import Count
from integration.models import ProcessedIntegrationEvent
from domains.event.models import EventRecord
from integration.handlers.events import EVENT_HANDLERS

def reconcile():
    total_pie = ProcessedIntegrationEvent.objects.count()
    print(f"1. ProcessedIntegrationEvent.objects.count() = {total_pie}")

    registered_types = list(EVENT_HANDLERS.keys())

    sum_proc = 0
    print("\n2. Breakdown per registered event_type in EventRecord:")
    for et in registered_types:
        matching_events = EventRecord.objects.filter(event_type=et)
        tot = matching_events.count()
        # Query used in audit script:
        proc = ProcessedIntegrationEvent.objects.filter(
            event_id__in=matching_events.values("id")
        ).count()
        sum_proc += proc
        print(f"  {et:28} | EventRecord: {tot:2} | matching ProcessedIntegrationEvent: {proc:2}")

    print(f"\nSum of matching ProcessedIntegrationEvent across registered types: {sum_proc}")

    # Check distinct event_id in ProcessedIntegrationEvent
    distinct_event_ids = ProcessedIntegrationEvent.objects.values("event_id").distinct().count()
    print(f"Distinct event_ids in ProcessedIntegrationEvent: {distinct_event_ids}")

    # Check duplicates in ProcessedIntegrationEvent (same event_id multiple rows)
    dups = ProcessedIntegrationEvent.objects.values("event_id").annotate(cnt=Count("id")).filter(cnt__gt=1)
    print(f"\nevent_ids with multiple rows in ProcessedIntegrationEvent: {dups.count()}")
    for d in dups:
        rows = list(ProcessedIntegrationEvent.objects.filter(event_id=d["event_id"]))
        ev = EventRecord.objects.filter(id=d["event_id"]).first()
        print(f"  event_id={d['event_id']} (ev.type={ev.event_type if ev else 'None'}) cnt={d['cnt']}")
        for r in rows:
            print(f"    row id={r.id} handler_name='{r.handler_name}' processed_at={r.processed_at}")

    # Check if there are ProcessedIntegrationEvent rows whose event_id is NOT in registered_types
    pie_events = EventRecord.objects.filter(id__in=ProcessedIntegrationEvent.objects.values("event_id"))
    pie_event_types = pie_events.values("event_type").annotate(cnt=Count("id"))
    print("\nEvent types of events in ProcessedIntegrationEvent:")
    for pet in pie_event_types:
        print(f"  {pet['event_type']}: {pet['cnt']}")

    # Check ProcessedIntegrationEvent rows whose handler_name does not match event_type or unregistered
    print("\nProcessedIntegrationEvent rows grouped by handler_name:")
    for ph in ProcessedIntegrationEvent.objects.values("handler_name").annotate(cnt=Count("id")):
        print(f"  handler_name='{ph['handler_name']}': {ph['cnt']}")

if __name__ == "__main__":
    reconcile()
