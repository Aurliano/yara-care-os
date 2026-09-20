import os
import sys
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from domains.care.models import CareActivity
from domains.scheduling.models import Occurrence

now = datetime.now(timezone.utc)
print(f"Current UTC time: {now.isoformat()}")

elder_id = "12f109ea-c412-4213-8c9c-039df25ff8cb"
activities = CareActivity.objects.filter(elder_id=elder_id)
print(f"CareActivities for elder: {activities.count()}")
for a in activities:
    print(f"  Activity: {a.id} status={a.status} title={a.display_title.encode('ascii', 'replace').decode('ascii')}")
    sched_id = a.schedule_definition_id
    if sched_id:
        occs = Occurrence.objects.filter(schedule_definition_id=sched_id).order_by('scheduled_for')
        print(f"    Occurrences ({occs.count()}):")
        for occ in occs:
            print(f"      occ={occ.id} status={occ.status} scheduled_for={occ.scheduled_for}")
