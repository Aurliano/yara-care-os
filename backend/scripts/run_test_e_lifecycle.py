import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from domains.care.models import CareActivity, Prescription
from domains.scheduling.models import ScheduleDefinition, Occurrence

ELDER_ID = "12f109ea-c412-4213-8c9c-039df25ff8cb"
WORKFLOW_ID = "c0a12480-46e3-4cc3-8393-f87e5ae28261"
ADB_PATH = r"C:\Users\AsA\AppData\Local\Android\Sdk\platform-tools\adb.exe"

print("==================================================")
print("TEST E: MEDICATION LIFECYCLE REGRESSION (NO RESTART)")
print("==================================================")

# Step 1: Auth
auth_req = urllib.request.Request(
    "http://127.0.0.1:8000/api/v1/auth/token/",
    data=json.dumps({"phone": "+989121111111", "password": "familylab123"}).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
auth_resp = urllib.request.urlopen(auth_req)
access_token = json.loads(auth_resp.read().decode("utf-8"))["access"]

# Clear logcat
subprocess.run([ADB_PATH, "-s", "33007668df77b293", "logcat", "-c"], check=True)

# Step 2: Check pre-test alarms
alarm_out = subprocess.check_output([ADB_PATH, "-s", "33007668df77b293", "shell", "dumpsys", "alarm"]).decode("utf-8", errors="ignore")
alarms_before = [l.strip() for l in alarm_out.splitlines() if "ir.sayda.yara.hub.action.OCCURRENCE_ALARM" in l or "ir.sayda.yara.hub" in l and "when" in l]
print(f"Pre-test Alarms in AlarmManager: {len(alarms_before)}")

# Step 3: T0 - Create new prescription
now = datetime.now(timezone.utc)
start_time = now + timedelta(hours=1)
payload = {
    "workflow_definition_id": WORKFLOW_ID,
    "recurrence_definition": {
        "type": "daily",
        "time": start_time.strftime("%H:%M"),
    },
    "timezone_name": "Asia/Tehran",
    "start_at": start_time.isoformat(),
    "display_title": "Calcium Test E",
    "medication_reference": "calcium-500",
    "dosage_information": "1 قرص",
    "elder_friendly_description": "قرص کلسیم بعد از ناهار",
}

print("\n--- STEP 1: CREATE PRESCRIPTION (T0) ---")
t0 = time.time()
t0_iso = datetime.now(timezone.utc).isoformat()
print(f"T0 Timestamp: {t0_iso}")

create_req = urllib.request.Request(
    f"http://127.0.0.1:8000/api/v1/elders/{ELDER_ID}/prescriptions/",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}
)
create_resp = urllib.request.urlopen(create_req)
presc_data = json.loads(create_resp.read().decode("utf-8"))
activity_id = presc_data["care_activity_id"]
print(f"Prescription Created: CareActivityID={activity_id}")

# Wait for Hub sync without restart (max 45s)
print("\nWaiting for Hub automatic foreground sync...")
synced = False
for i in range(45):
    time.sleep(1)
    # Check logcat for applied replica change
    logs = subprocess.check_output([ADB_PATH, "-s", "33007668df77b293", "logcat", "-d"]).decode("utf-8", errors="ignore")
    if activity_id in logs or "Calcium Test E" in logs or "sync.session.completed" in logs:
        t7 = time.time()
        print(f"T7: Hub synced new medication at {datetime.now(timezone.utc).isoformat()} (Latency: {t7 - t0:.1f}s)")
        synced = True
        break

if not synced:
    print("Warning: Auto-sync did not trigger in 45s, checking logs...")

# Check alarms after create
time.sleep(2)
alarm_out_mid = subprocess.check_output([ADB_PATH, "-s", "33007668df77b293", "shell", "dumpsys", "alarm"]).decode("utf-8", errors="ignore")
alarms_mid = [l.strip() for l in alarm_out_mid.splitlines() if "ir.sayda.yara.hub.action.OCCURRENCE_ALARM" in l or "ir.sayda.yara.hub" in l and "when" in l]
print(f"Alarms After Create: {len(alarms_mid)}")

# Step 4: Cancel the medication
print(f"\n--- STEP 2: CANCEL PRESCRIPTION (Activity ID: {activity_id}) ---")
t_cancel_0 = time.time()
cancel_req = urllib.request.Request(
    f"http://127.0.0.1:8000/api/v1/care-activities/{activity_id}/end/",
    data=json.dumps({}).encode("utf-8"),
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}
)
cancel_resp = urllib.request.urlopen(cancel_req)
print(f"Cancellation HTTP Status: {cancel_resp.status}")

# Wait for Hub to sync cancellation without restart
print("Waiting for Hub to sync cancellation...")
cancel_synced = False
for i in range(45):
    time.sleep(1)
    logs = subprocess.check_output([ADB_PATH, "-s", "33007668df77b293", "logcat", "-d"]).decode("utf-8", errors="ignore")
    if "CANCELLED" in logs or "care_activity.ended" in logs or "sync.session.completed" in logs:
        print(f"Cancellation synced at {datetime.now(timezone.utc).isoformat()} (Latency: {time.time() - t_cancel_0:.1f}s)")
        cancel_synced = True
        break

# Check alarms after cancel
time.sleep(2)
alarm_out_after = subprocess.check_output([ADB_PATH, "-s", "33007668df77b293", "shell", "dumpsys", "alarm"]).decode("utf-8", errors="ignore")
alarms_after = [l.strip() for l in alarm_out_after.splitlines() if "ir.sayda.yara.hub.action.OCCURRENCE_ALARM" in l or "ir.sayda.yara.hub" in l and "when" in l]
print(f"Alarms After Cancel: {len(alarms_after)}")

print("\n--- TEST E LIFECYCLE SUMMARY ---")
print(f"Pre-Create Alarms: {len(alarms_before)}")
print(f"Post-Create Alarms: {len(alarms_mid)}")
print(f"Post-Cancel Alarms: {len(alarms_after)}")
print("TEST E COMPLETED WITHOUT APP RESTART.")
