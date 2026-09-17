import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from domains.care.models import CareActivity, Prescription
from domains.scheduling.models import ScheduleDefinition, Occurrence
from domains.synchronization.models import ReplicaState, SynchronizationSession, SynchronizationOperation

ELDER_ID = "12f109ea-c412-4213-8c9c-039df25ff8cb"
DEVICE_ID = "d6b1fcc4-d5d9-4729-bb15-c3b6acc00e88"
REPLICA_ID = "f0d192ae-1a71-4902-9655-77467c16043b"
ADB_PATH = r"C:\Users\AsA\AppData\Local\Android\Sdk\platform-tools\adb.exe"

print("==================================================")
print("TASK 2.1 - CONTROLLED MEDICATION MUTATION TEST")
print("==================================================")

# Step 1: Baseline Check
print("\n--- BASELINE CHECK ---")
replica = ReplicaState.objects.get(replica_identifier=REPLICA_ID)
print(f"Backend Replica Checkpoint: {replica.checkpoint_sequence}")
baseline_activities = list(CareActivity.objects.filter(elder_id=ELDER_ID).values("id", "display_title", "status", "aggregate_version"))
print(f"Baseline Care Activities ({len(baseline_activities)}):")
for a in baseline_activities:
    print(f"  {a['id']} - {a['display_title']} (v={a['aggregate_version']}, {a['status']})")

# Check current alarms via adb
alarm_out = subprocess.check_output([ADB_PATH, "-s", "33007668df77b293", "shell", "dumpsys alarm"]).decode("utf-8", errors="ignore")
hub_alarms = [line.strip() for line in alarm_out.splitlines() if "ir.sayda.yara.hub.action.OCCURRENCE_ALARM" in line or "when 1789" in line and "ir.sayda.yara.hub" in line]
print(f"Hub Registered Alarms Count: {len(hub_alarms)}")

# Step 2: Caregiver Authentication
print("\n--- CAREGIVER AUTHENTICATION ---")
auth_req = urllib.request.Request(
    "http://127.0.0.1:8000/api/v1/auth/token/",
    data=json.dumps({"phone": "+989121111111", "password": "familylab123"}).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
auth_resp = urllib.request.urlopen(auth_req)
tokens = json.loads(auth_resp.read().decode("utf-8"))
access_token = tokens["access"]
print("Caregiver JWT obtained.")

# Clear adb logcat buffer before mutation
subprocess.run([ADB_PATH, "-s", "33007668df77b293", "logcat", "-c"], check=True)

# Step 3: T0 - Create Medication Mutation
print("\n--- T0: POSTING NEW PRESCRIPTION ---")
t0 = time.time()
t0_iso = datetime.now(timezone.utc).isoformat()
print(f"T0 Timestamp: {t0_iso} ({t0})")

create_payload = {
    "workflow_definition_id": "78b24afe-e7f1-4522-b7ea-a558e77637e3",
    "recurrence_definition": {"type": "daily", "time": "20:30"},
    "timezone_name": "Asia/Tehran",
    "start_at": "2026-09-17T00:00:00Z",
    "display_title": "Evening Calcium",
    "display_subtitle": "1 قرص با آب",
    "medication_reference": "med-calcium-500",
    "dosage_information": "1 قرص بعد از شام",
    "elder_friendly_description": "قرص کلسیم بعد از شام با یک لیوان آب",
}

create_req = urllib.request.Request(
    f"http://127.0.0.1:8000/api/v1/elders/{ELDER_ID}/prescriptions/",
    data=json.dumps(create_payload).encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
)
create_resp = urllib.request.urlopen(create_req)
created_data = json.loads(create_resp.read().decode("utf-8"))

print(f"Mutation Response (HTTP {create_resp.status}):")
print(json.dumps(created_data, indent=2, ensure_ascii=False))

new_activity_id = created_data.get("care_activity_id")
new_activity = CareActivity.objects.get(pk=new_activity_id)
print(f"\nBackend Verification:")
print(f"  CareActivity ID: {new_activity.id}")
print(f"  Title: {new_activity.display_title}")
print(f"  Status: {new_activity.status}")
print(f"  Aggregate Version: {new_activity.aggregate_version}")
print(f"  Schedule Definition ID: {new_activity.schedule_definition_id}")
new_occurrences = list(Occurrence.objects.filter(schedule_definition_id=new_activity.schedule_definition_id).order_by("scheduled_for"))
print(f"  Occurrences Generated: {len(new_occurrences)}")
for o in new_occurrences[:5]:
    print(f"    Occurrence {o.id} at {o.scheduled_for} ({o.status})")

# Step 4: Trace Download Sync and Hub Application
print("\n--- WAITING FOR FOREGROUND SYNC & HUB PROPAGATION ---")
print("Polling logcat and backend sync sessions (timeout 45s)...")

t1 = None
t2 = None
t3 = None
t4 = None
t5 = None
t6 = None
t7 = None

start_wait = time.time()
while time.time() - start_wait < 45:
    time.sleep(1)
    # Check logcat
    logcat_proc = subprocess.run([ADB_PATH, "-s", "33007668df77b293", "logcat", "-d"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    lines = logcat_proc.stdout.decode("utf-8", errors="ignore").splitlines()
    for line in lines:
        if "sync.session.started" in line and t1 is None:
            t1 = time.time()
            print(f"  [T1/T2] Hub sync started: {line.strip()}")
        if "replica.operation.received" in line and str(new_activity_id) in line and t3 is None:
            t3 = time.time()
            print(f"  [T3] Operation received for new activity: {line.strip()}")
        if "replica.operation.applied" in line and str(new_activity_id) in line and t4 is None:
            t4 = time.time()
            print(f"  [T4] Operation applied for new activity: {line.strip()}")
        if "sync.session.completed" in line and t4 is not None and t5 is None:
            t5 = time.time()
            print(f"  [T5] Sync session completed: {line.strip()}")
            break
    if t5 is not None:
        break

# Wait 2 seconds for Room and UI emission
time.sleep(2)
t6 = time.time()

# Check AlarmManager on device
alarm_out_after = subprocess.check_output([ADB_PATH, "-s", "33007668df77b293", "shell", "dumpsys alarm"]).decode("utf-8", errors="ignore")
hub_alarms_after = [line.strip() for line in alarm_out_after.splitlines() if "ir.sayda.yara.hub.action.OCCURRENCE_ALARM" in line or "when 1789" in line and "ir.sayda.yara.hub" in line]
print(f"\nAlarms After Mutation: {len(hub_alarms_after)} (was {len(hub_alarms)})")

# Capture screenshot of running Hub without restart
print("\nCapturing tablet screenshot of RUNNING Hub (NO RESTART)...")
subprocess.run([ADB_PATH, "-s", "33007668df77b293", "shell", "screencap -p /sdcard/screen_after_t0.png"], check=True)
subprocess.run([ADB_PATH, "-s", "33007668df77b293", "pull", "/sdcard/screen_after_t0.png", r"c:\yara-care-os\tablet_screen_after_t0.png"], check=True)

# Also tap "مشاهده برنامه" (View Schedule) to verify modal
subprocess.run([ADB_PATH, "-s", "33007668df77b293", "shell", "input tap 1680 590; sleep 1; screencap -p /sdcard/screen_med_after_t0.png"], check=True)
subprocess.run([ADB_PATH, "-s", "33007668df77b293", "pull", "/sdcard/screen_med_after_t0.png", r"c:\yara-care-os\tablet_screen_med_after_t0.png"], check=True)
# Dismiss modal
subprocess.run([ADB_PATH, "-s", "33007668df77b293", "shell", "input keyevent 4"], check=True)

# Check replica in backend
replica.refresh_from_db()
print(f"\nBackend Replica Checkpoint After: {replica.checkpoint_sequence}")
latest_session = SynchronizationSession.objects.filter(replica_state=replica, direction="DOWNLOAD").order_by("-created_at").first()
if latest_session:
    print(f"Latest Download Session: {latest_session.id} ({latest_session.status})")
    for op in latest_session.operations.all():
        print(f"  Op: {op.operation_type} - agg={op.aggregate_reference} ver={op.aggregate_version} status={op.status}")

print("\n=== TIMING REPORT ===")
print(f"T0 (Mutation): {t0}")
print(f"T1 (Sync Trigger / Start): {t1} (Latency from T0: {round(t1 - t0, 2) if t1 else 'N/A'}s)")
print(f"T3 (Operation Received): {t3} (Latency from T0: {round(t3 - t0, 2) if t3 else 'N/A'}s)")
print(f"T4 (Operation Applied): {t4} (Latency from T0: {round(t4 - t0, 2) if t4 else 'N/A'}s)")
print(f"T5 (Sync Session Completed): {t5} (Latency from T0: {round(t5 - t0, 2) if t5 else 'N/A'}s)")
print(f"T6 (Alarm / UI State Check): {t6}")
