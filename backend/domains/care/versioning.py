"""Care aggregate version ownership for synchronization."""

from __future__ import annotations

from domains.care.models import CareActivity


def bump_care_activity_version(activity: CareActivity, update_fields: list[str]) -> list[str]:
    """Increment monotonic aggregate version owned by Care."""
    activity.aggregate_version += 1
    if "aggregate_version" not in update_fields:
        update_fields.append("aggregate_version")
    return update_fields
