"""Due-time processing for occurrences."""

from __future__ import annotations

from datetime import datetime

from django.db import transaction
from django.utils import timezone

from domains.scheduling.enums import OccurrenceStatus
from domains.scheduling.models import Occurrence
from domains.scheduling.services.events import emit_occurrence_due


@transaction.atomic
def mark_occurrence_due(occurrence: Occurrence, *, occurred_at: datetime | None = None) -> Occurrence:
    """Transition SCHEDULED -> DUE and record OccurrenceDue in one transaction.

    If event recording fails, the DUE transition is rolled back.
    """
    occurrence = Occurrence.objects.select_for_update().get(pk=occurrence.pk)
    if occurrence.status in {
        OccurrenceStatus.CANCELLED,
        OccurrenceStatus.SKIPPED,
        OccurrenceStatus.DUE,
    }:
        return occurrence

    if occurrence.status != OccurrenceStatus.SCHEDULED:
        return occurrence

    occurred_at = occurred_at or timezone.now()
    occurrence.status = OccurrenceStatus.DUE
    occurrence.save(update_fields=["status"])
    emit_occurrence_due(
        occurrence_id=occurrence.id,
        schedule_definition_id=occurrence.schedule_definition_id,
        scheduled_for=occurrence.scheduled_for,
        occurred_at=occurred_at,
    )
    return occurrence


def process_due_occurrences(*, now: datetime | None = None) -> int:
    """Transition eligible SCHEDULED occurrences to DUE. Idempotent."""
    now = now or timezone.now()
    processed = 0
    due_candidate_ids = list(
        Occurrence.objects.filter(
            status=OccurrenceStatus.SCHEDULED,
            scheduled_for__lte=now,
        ).values_list("pk", flat=True)
    )
    for occurrence_id in due_candidate_ids:
        occurrence = Occurrence.objects.get(pk=occurrence_id)
        if occurrence.status != OccurrenceStatus.SCHEDULED:
            continue
        mark_occurrence_due(occurrence, occurred_at=now)
        processed += 1
    return processed
