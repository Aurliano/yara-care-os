"""Signals connecting Care aggregate_version invalidation to Scheduling mutations."""

from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender="scheduling.ScheduleException")
def on_schedule_exception_saved(sender, instance, **kwargs):
    """Bumps version on ScheduleException creation or update."""
    from domains.care.services.activities import bump_care_activity_version_for_schedule

    bump_care_activity_version_for_schedule(instance.schedule_definition_id)


@receiver(post_save, sender="scheduling.Occurrence")
def on_occurrence_saved(sender, instance, update_fields=None, **kwargs):
    """Bumps version on direct Occurrence status or schedule mutations."""
    if getattr(instance, "_from_schedule_exception", False):
        return

    if update_fields and ("status" in update_fields or "scheduled_for" in update_fields):
        from domains.care.services.activities import bump_care_activity_version_for_schedule

        bump_care_activity_version_for_schedule(instance.schedule_definition_id)
