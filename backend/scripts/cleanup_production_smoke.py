"""One-off production cleanup script to ensure smoke test records are purged."""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
django.setup()

from domains.device.models import Device
from domains.synchronization.models import ReplicaState

d_count = Device.objects.filter(serial_number="TEST-SMOKE-123").delete()[0]
r_count = ReplicaState.objects.filter(
    replica_identifier="02e02ff9-fe61-4ee9-8d1b-6b40c4ebdd97"
).delete()[0]
print(f"CLEANED_UP: device={d_count}, replica={r_count}")
