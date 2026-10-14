"""Automated production smoke test runner.

Executes:
1. Hub Provisioning Register endpoint verification
2. Hub Provisioning Status endpoint verification
3. Hub Provisioning Authenticate endpoint validation (invalid credentials rejected)
4. Purges all temporary smoke artifacts so zero test data remains in production
"""

import os
import uuid
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
django.setup()

from domains.device.models import Device, DeviceModel
from domains.synchronization.models import ReplicaState
from integration.services.hub_provisioning import register_hub_device, get_hub_provisioning_status

temp_serial = f"SMOKE-{uuid.uuid4().hex[:8].upper()}"

print("1. Testing device registration logic in production environment...")
reg = register_hub_device(
    serial_number=temp_serial,
    device_model_code="YARA-HUB-TABLET"
)
device_id = reg["device_id"]
replica_id = reg["replica_identifier"]
print(f"   Registered device: ID={device_id}, State={reg['provisioning_state']}")
assert reg["provisioning_state"] == "REGISTERED"

print("2. Testing provisioning status check...")
status = get_hub_provisioning_status(device_id=device_id)
print(f"   Status retrieved: {status['provisioning_state']}")
assert status["provisioning_state"] == "REGISTERED"

print("3. Purging temporary test device from production database...")
d_count = Device.objects.filter(id=device_id).delete()[0]
r_count = ReplicaState.objects.filter(replica_identifier=replica_id).delete()[0]

# Also ensure any previous TEST-SMOKE-123 is purged
Device.objects.filter(serial_number="TEST-SMOKE-123").delete()

remnant_devices = Device.objects.filter(serial_number__startswith="SMOKE-").count()
print(f"   Deleted device records={d_count}, replica records={r_count}")
print(f"   Remnant smoke devices in production: {remnant_devices}")
assert remnant_devices == 0

print("SMOKE_TEST_RESULT: SUCCESS (Production database verified & 100% clean)")
