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

ACTIVITY_ID = "99900e46-8525-4120-a2b2-7a5629e53efc"
REPLICA_ID = "f0d192ae-1a71-4902-9655-77467c16043b"
ADB_PATH = r"C:\Users\AsA\AppData\Local\Android\Sdk\platform-tools\adb.exe"

print("==================================================")
print("TASK 2.1 - CONTROLLED CANCELLATION TEST")
print("==================================================")

# Step 1: Pre-cancellation State
activity = CareActivity.objects.get(pk=ACTIVITY_ID)
schedule = activity.schedule_definition
replica = ReplicaState.objects.get(replica_identifier=REPLICA_ID)
print(f"Target Activity: {activity.id} ({activity.display_title})")
print(f"  Status: {activity.status}, Version: {activity.aggregate_version}")
print(f"  Schedule: {schedule.id}, Schedule Status: {schedule.status}")
print(f"  Backend Replica Checkpoint: {replica.checkpoint_sequence}")

alarm_out_before = subprocess.check_output([ADB_PATH, "-s", "33007668df77b293", "shell", "dumpsys alarm"]).decode("utf-8", errors="ignore")
hub_alarms_before = [line.strip() for line in alarm_out_before.splitlines() if "ir.sayda.yara.hub.action.OCCURRENCE_ALARM" in line or "when 1789" in line and "ir.sayda.yara.hub" in line]
print(f"Hub Registered Alarms Before Cancel: {len(hub_alarms_before)}")

# Step 2: Auth
auth_req = urllib.request.Request(
    "http://127.0.0.1:8000/api/v1/auth/token/",
    data=json.dumps({"phone": "+989121111111", "password": "familylab123"}).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
auth_resp = urllib.request.urlopen(auth_req)
tokens = json.loads(auth_resp.read().decode("utf-8"))
access_token = tokens["access"]

# Clear logcat buffer
subprocess.run([ADB_PATH, "-s", "33007668df77b293", "logcat", "-c"], check=True)

# Step 3: T0 - End/Cancel CareActivity
print("\n--- T0: ENDING CARE ACTIVITY ---")
t0 = time.time()
t0_iso = datetime.now(timezone.utc).isoformat()
print(f"T0 Timestamp: {t0_iso} ({t0})")

end_req = urllib.request.Request(
    f"http://127.0.0.1:8000/api/v1/care-activities/{ACTIVITY_ID}/end/",
    data=b"{}",
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
)
end_resp = urllib.request.urlopen(end_req)
ended_data = json.loads(end_resp.read().decode("utf-8"))
print(f"End Response (HTTP {end_resp.status}):")
print(json.dumps(ended_data, indent=2, ensure_ascii=False))

# Verify backend state
activity.refresh_from_db()
schedule.refresh_from_db()
print(f"\nBackend Verification After End:")
print(f"  Activity Status: {activity.status}")
print(f"  Activity Version: {activity.aggregate_version} (was 1)")
print(f"  Schedule Status: {schedule.status} (was ACTIVE)")

# Step 4: Trace Download Sync and Hub Application
print("\n--- WAITING FOR FOREGROUND SYNC & HUB CANCELLATION PROPAGATION ---")
t1 = None
t3 = None
t4 = None
t5 = None

start_wait = time.time()
while time.time() - start_wait < 45:
    time.sleep(1)
    logcat_proc = subprocess.run([ADB_PATH, "-s", "33007668df77b293", "logcat", "-d"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    lines = logcat_proc.stdout.decode("utf-8", errors="ignore").splitlines()
    for line in lines:
        if "sync.session.started" in line and t1 is None:
            t1 = time.time()
            print(f"  [T1/T2] Hub sync started: {line.strip()}")
        if "replica.operation.received" in line and str(ACTIVITY_ID) in line and t3 is None:
            t3 = time.time()
            print(f"  [T3] Operation received for activity: {line.strip()}")
        if "replica.operation.applied" in line and str(ACTIVITY_ID) in line and t4 is None:
            t4 = time.time()
            print(f"  [T4] Operation applied for activity: {line.strip()}")
        if "sync.session.completed" in line and t4 is not None and t5 is None:
            t5 = time.time()
            print(f"  [T5] Sync session completed: {line.strip()}")
            break
    if t5 is not None:
        break

time.sleep(2)
t6 = time.time()

# Check AlarmManager on device
alarm_out_after = subprocess.check_output([ADB_PATH, "-s", "33007668df77b293", "shell", "dumpsys alarm"]).decode("utf-8", errors="ignore")
hub_alarms_after = [line.strip() for line in alarm_out_after.splitlines() if "ir.sayda.yara.hub.action.OCCURRENCE_ALARM" in line or "when 1789" in line and "ir.sayda.yara.hub" in line]
print(f"\nAlarms After Cancel: {len(hub_alarms_after)} (was {len(hub_alarms_before)})")

# Capture screenshot of running Hub without restart
print("\nCapturing tablet screenshot after cancellation (NO RESTART)...")
subprocess.run([ADB_PATH, "-s", "33007668df77b293", "shell", "screencap -p /sdcard/screen_after_cancel.png"], check=True)
subprocess.run([ADB_PATH, "-s", "33007668df77b293", "pull", "/sdcard/screen_after_cancel.png", r"c:\yara-care-os\tablet_screen_after_cancel.png"], check=True)

# Also tap "مشاهده برنامه" (View Schedule) to verify modal
subprocess.run([ADB_PATH, "-s", "33007668df77b293", "shell", "input tap 1680 590; sleep 1; screencap -p /sdcard/screen_med_after_cancel.png"], check=True)
subprocess.run([ADB_PATH, "-s", "33007668df77b293", "pull", "/sdcard/screen_med_after_cancel.png", r"c:\yara-care-os\tablet_screen_med_after_cancel.png"], check=True)
subprocess.run([ADB_PATH, "-s", "33007668df77b293", "shell", "input keyevent 4"], check=True)

# Check replica in backend
replica.refresh_from_db()
print(f"\nBackend Replica Checkpoint After Cancel: {replica.checkpoint_sequence}")
latest_session = SynchronizationSession.objects.filter(replica_state=replica, direction="DOWNLOAD").order_by("-created_at").first()
if latest_session:
    print(f"Latest Download Session: {latest_session.id} ({latest_session.status})")
    for op in latest_session.operations.all():
        print(f"  Op: {op.operation_type} - agg={op.aggregate_reference} ver={op.aggregate_version} status={op.status}")

print("\n=== CANCELLATION TIMING REPORT ===")
print(f"T0 (End CareActivity): {t0}")
print(f"T1 (Sync Trigger / Start): {t1} (Latency from T0: {round(t1 - t0, 2) if t1 else 'N/A'}s)")
print(f"T3 (Operation Received): {t3} (Latency from T0: {round(t3 - t0, 2) if t3 else 'N/A'}s)")
print(f"T4 (Operation Applied): {t4} (Latency from T0: {round(t4 - t0, 2) if t4 else 'N/A'}s)")
print(f"T5 (Sync Session Completed): {t5} (Latency from T0: {round(t5 - t0, 2) if t5 else 'N/A'}s)")
print(f"T6 (Alarm / UI State Check): {t6}")
