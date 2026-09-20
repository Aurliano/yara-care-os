import os
import sys
sys.stdout.reconfigure(encoding="utf-8")
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from domains.identity_access.models import Elder
from domains.care.models import CareActivity, CareCompletion
from domains.scheduling.models import Occurrence
from domains.workflow.models import WorkflowExecution, ConfirmationEvidence

elder_id = "12f109ea-c412-4213-8c9c-039df25ff8cb"
elder = Elder.objects.filter(id=elder_id).first()
print(f"Elder: {elder.id if elder else 'None'} ({elder.full_name if elder else 'None'})")

activities = CareActivity.objects.filter(elder_id=elder_id)
for a in activities:
    print(f"\nActivity: {a.id} \"{a.display_title}\" status={a.status} type={a.activity_type}")
    occs = Occurrence.objects.filter(
        schedule_definition_id=a.schedule_definition_id,
        scheduled_for__gte="2026-09-18T00:00:00Z",
        scheduled_for__lte="2026-09-22T00:00:00Z",
    ).order_by("scheduled_for")
    for o in occs:
        print(f"   Occ: {o.id} time={o.scheduled_for} status={o.status}")
        wfs = WorkflowExecution.objects.filter(occurrence_id=o.id)
        for w in wfs:
            print(f"       WF: {w.id} status={w.status} completed_at={w.completed_at}")
            evs = ConfirmationEvidence.objects.filter(workflow_execution=w)
            for ev in evs:
                print(f"           Evidence: {ev.evidence_type} ref={ev.source_reference} source={ev.source_type}")
        comps = CareCompletion.objects.filter(occurrence_id=o.id)
        for c in comps:
            print(f"       Completion: {c.id} state={c.completion_state} at={c.interpreted_at}")
