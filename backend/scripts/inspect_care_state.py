import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from domains.care.models import CareActivity, Prescription
from domains.scheduling.models import ScheduleDefinition, Occurrence
from domains.synchronization.models import ReplicaState, SynchronizationSession

elder_id = "12f109ea-c412-4213-8c9c-039df25ff8cb"
print(f"=== ELDER {elder_id} BASELINE ===")

print("\n--- CARE ACTIVITIES ---")
for a in CareActivity.objects.filter(elder_id=elder_id):
    print(f"Activity ID: {a.id}")
    print(f"  Title: {a.display_title}")
    print(f"  Status: {a.status}")
    print(f"  Aggregate Version: {a.aggregate_version}")
    print(f"  Schedule Definition ID: {a.schedule_definition_id}")

print("\n--- PRESCRIPTIONS ---")
for p in Prescription.objects.filter(care_activity__elder_id=elder_id):
    print(f"Prescription (care_activity_id): {p.care_activity_id}")
    print(f"  Medication: {p.medication_reference}")
    print(f"  Dosage: {p.dosage_information}")
    print(f"  Elder Description: {p.elder_friendly_description}")

print("\n--- SCHEDULE DEFINITIONS ---")
for s in ScheduleDefinition.objects.filter(care_activity__elder_id=elder_id):
    print(f"Schedule ID: {s.id}")
    print(f"  Status: {s.status}")
    print(f"  Recurrence: {s.recurrence_definition}")
    print(f"  Start: {s.start_at}, End: {s.end_at}")

print("\n--- OCCURRENCES ---")
for o in Occurrence.objects.filter(schedule_definition__care_activity__elder_id=elder_id).order_by("scheduled_for"):
    print(f"Occurrence ID: {o.id}")
    print(f"  Schedule ID: {o.schedule_definition_id}")
    print(f"  Scheduled For: {o.scheduled_for}")
    print(f"  Status: {o.status}")

print("\n--- REPLICAS ---")
for r in ReplicaState.objects.all():
    print(f"Replica Identifier: {r.replica_identifier}")
    print(f"  Health: {r.health}")
    print(f"  Status: {r.status}")
    print(f"  Checkpoint: {r.checkpoint_sequence}")
    print(f"  Last Successful Sync: {r.last_successful_sync}")

print("\n--- LATEST SYNC SESSIONS ---")
for s in SynchronizationSession.objects.filter(replica_state__replica_identifier="f0d192ae-1a71-4902-9655-77467c16043b").order_by("-created_at")[:5]:
    print(f"Session ID: {s.id}")
    print(f"  Direction: {s.direction}")
    print(f"  Status: {s.status}")
    print(f"  Started: {s.started_at}, Completed: {s.completed_at}")
    for op in s.operations.all():
        print(f"    Op: type={op.operation_type}, agg={op.aggregate_reference}, ver={op.aggregate_version}, status={op.status}")
