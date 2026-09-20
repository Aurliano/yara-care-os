import os
import sys
import uuid
import django

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.db.models import Count, Min, Max
from domains.event.models import EventRecord
from integration.models import ProcessedIntegrationEvent
from integration.handlers.events import EVENT_HANDLERS
from domains.care.models import CareCompletion, CareActivity
from domains.scheduling.models import Occurrence
from domains.workflow.models import WorkflowExecution
from domains.notification.models import CaregiverAlert

def run_audit():
    print("=" * 70)
    print("AUDIT: REGISTERED EVENT_HANDLERS IN INTEGRATION")
    print("=" * 70)
    registered_types = list(EVENT_HANDLERS.keys())
    for r in registered_types:
        print(f"  - {r} -> {EVENT_HANDLERS[r].__name__}")

    processed_ids = ProcessedIntegrationEvent.objects.values("event_id")

    # All events in EventRecord
    total_events = EventRecord.objects.count()
    print(f"\nTotal EventRecord in DB: {total_events}")
    
    # All processed integration events
    total_processed = ProcessedIntegrationEvent.objects.count()
    print(f"Total ProcessedIntegrationEvent in DB: {total_processed}")

    # Pending integration events
    pending_qs = EventRecord.objects.filter(
        event_type__in=registered_types
    ).exclude(
        id__in=processed_ids
    )

    total_pending = pending_qs.count()
    print(f"\nTotal pending registered integration events: {total_pending}")

    breakdown = list(
        pending_qs.values("event_type")
        .annotate(count=Count("id"), oldest=Min("recorded_at"), newest=Max("recorded_at"))
        .order_by("event_type")
    )

    print("\nPending Breakdown by Event Type:")
    if not breakdown:
        print("  NONE! (0 pending registered integration events)")
    for b in breakdown:
        print(f"  Event Type: {b['event_type']}")
        print(f"    Count:  {b['count']}")
        print(f"    Oldest: {b['oldest']}")
        print(f"    Newest: {b['newest']}")

    # Let's inspect all event types in EventRecord (including unregistered)
    print("\nAll Event Types present in EventRecord table:")
    all_types = list(
        EventRecord.objects.values("event_type")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    for at in all_types:
        is_reg = "REGISTERED" if at["event_type"] in registered_types else "unregistered"
        p_count = ProcessedIntegrationEvent.objects.filter(handler_name=at["event_type"]).count()
        print(f"  {at['event_type']:32} | total: {at['total']:5} | registered: {is_reg:12} | processed: {p_count:5}")

    # For each registered type, check how many total exist vs processed
    print("\nRegistered Types Status:")
    for et in registered_types:
        tot = EventRecord.objects.filter(event_type=et).count()
        proc = ProcessedIntegrationEvent.objects.filter(
            event_id__in=EventRecord.objects.filter(event_type=et).values("id")
        ).count()
        pending = tot - proc
        print(f"  {et:30} | total: {tot:4} | processed: {proc:4} | pending: {pending:4}")

    # Detailed check of side-effects for every registered event
    print("\n" + "=" * 70)
    print("SIDE-EFFECT AUDIT FOR REGISTERED EVENTS")
    print("=" * 70)

    # 1. OccurrenceDue
    print("\n[1] OccurrenceDue:")
    for ev in EventRecord.objects.filter(event_type="OccurrenceDue").order_by("recorded_at"):
        occ_id = ev.payload.get("occurrence_id")
        wf_exec = WorkflowExecution.objects.filter(occurrence_id=occ_id).first() if occ_id else None
        print(f"  Event {ev.id} at {ev.recorded_at}: occurrence_id={occ_id}")
        print(f"    WorkflowExecution: {wf_exec.id if wf_exec else 'None'} (status: {wf_exec.status if wf_exec else 'N/A'})")

    # 2. ExecutionStarted
    print("\n[2] ExecutionStarted:")
    for ev in EventRecord.objects.filter(event_type="ExecutionStarted").order_by("recorded_at"):
        wf_id = ev.payload.get("workflow_execution_id")
        wf_exec = WorkflowExecution.objects.filter(id=wf_id).first() if wf_id else None
        print(f"  Event {ev.id} at {ev.recorded_at}: wf_id={wf_id}, exists={wf_exec is not None}")

    # 3. ExecutionConfirmed
    print("\n[3] ExecutionConfirmed:")
    for ev in EventRecord.objects.filter(event_type="ExecutionConfirmed").order_by("recorded_at"):
        wf_id = ev.payload.get("workflow_execution_id")
        wf_exec = WorkflowExecution.objects.filter(id=wf_id).first() if wf_id else None
        completion = CareCompletion.objects.filter(workflow_execution_id=wf_id).first() if wf_id else None
        print(f"  Event {ev.id} at {ev.recorded_at}: wf_id={wf_id}")
        print(f"    WF status: {wf_exec.status if wf_exec else 'None'}")
        print(f"    CareCompletion: {completion.id if completion else 'MISSING!'} state={completion.completion_state if completion else 'N/A'}")

    # 4. ExecutionMissed
    print("\n[4] ExecutionMissed:")
    for ev in EventRecord.objects.filter(event_type="ExecutionMissed").order_by("recorded_at"):
        wf_id = ev.payload.get("workflow_execution_id")
        wf_exec = WorkflowExecution.objects.filter(id=wf_id).first() if wf_id else None
        completion = CareCompletion.objects.filter(workflow_execution_id=wf_id).first() if wf_id else None
        print(f"  Event {ev.id} at {ev.recorded_at}: wf_id={wf_id}")
        print(f"    WF status: {wf_exec.status if wf_exec else 'None'}")
        print(f"    CareCompletion: {completion.id if completion else 'MISSING!'} state={completion.completion_state if completion else 'N/A'}")

    # 5. CommunicationSessionEnded
    print("\n[5] CommunicationSessionEnded:")
    for ev in EventRecord.objects.filter(event_type="CommunicationSessionEnded").order_by("recorded_at"):
        ext_ref = ev.payload.get("external_execution_reference")
        outcome = ev.payload.get("outcome")
        print(f"  Event {ev.id} at {ev.recorded_at}: ext_ref={ext_ref}, outcome={outcome}")

    # 6. MedicationTaken
    print("\n[6] MedicationTaken:")
    for ev in EventRecord.objects.filter(event_type="MedicationTaken").order_by("recorded_at"):
        act_id = ev.payload.get("care_activity_id")
        comp_id = ev.payload.get("care_completion_id")
        comp = CareCompletion.objects.filter(id=comp_id).first() if comp_id else None
        print(f"  Event {ev.id} at {ev.recorded_at}: activity_id={act_id}, completion_id={comp_id}")
        print(f"    Completion exists: {comp is not None} (state: {comp.completion_state if comp else 'N/A'})")

    # 7. MedicationMissed
    print("\n[7] MedicationMissed:")
    for ev in EventRecord.objects.filter(event_type="MedicationMissed").order_by("recorded_at"):
        act_id = ev.payload.get("care_activity_id")
        comp_id = ev.payload.get("care_completion_id")
        comp = CareCompletion.objects.filter(id=comp_id).first() if comp_id else None
        alert = CaregiverAlert.objects.filter(source_reference=str(comp_id)).first() if comp_id else None
        print(f"  Event {ev.id} at {ev.recorded_at}: activity_id={act_id}, completion_id={comp_id}")
        print(f"    Completion exists: {comp is not None}")
        print(f"    CaregiverAlert: {alert.id if alert else 'None'} title='{alert.title if alert else 'N/A'}'")


if __name__ == "__main__":
    run_audit()
