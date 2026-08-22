"""Caregiver alert commands and queries."""

from __future__ import annotations

import uuid
from datetime import datetime

from django.db import IntegrityError, transaction
from django.utils import timezone

from domains.identity_access.models import Elder
from domains.notification.enums import AlertSeverity
from domains.notification.exceptions import AlertNotFoundError, ElderNotFoundError
from domains.notification.models import CaregiverAlert


def _ensure_elder_exists(elder_id: uuid.UUID) -> Elder:
    try:
        return Elder.objects.get(pk=elder_id)
    except Elder.DoesNotExist as exc:
        raise ElderNotFoundError("Elder not found.") from exc


@transaction.atomic
def record_caregiver_alert(
    *,
    elder_id: uuid.UUID,
    title: str,
    body: str,
    severity: str,
    source_type: str,
    source_reference: str,
    occurred_at: datetime | None = None,
) -> CaregiverAlert:
    _ensure_elder_exists(elder_id)
    if severity not in AlertSeverity.values:
        raise ValueError(f"Unsupported alert severity: {severity}")
    existing = CaregiverAlert.objects.filter(
        source_type=source_type,
        source_reference=source_reference,
    ).first()
    if existing is not None:
        return existing
    occurred_at = occurred_at or timezone.now()
    try:
        return CaregiverAlert.objects.create(
            elder_id=elder_id,
            title=title,
            body=body,
            severity=severity,
            occurred_at=occurred_at,
            source_type=source_type,
            source_reference=source_reference,
        )
    except IntegrityError:
        return CaregiverAlert.objects.get(
            source_type=source_type,
            source_reference=source_reference,
        )


def list_elder_alerts(*, elder_id: uuid.UUID) -> list[CaregiverAlert]:
    _ensure_elder_exists(elder_id)
    return list(
        CaregiverAlert.objects.filter(elder_id=elder_id).order_by("-occurred_at", "-created_at")
    )


def get_alert(*, elder_id: uuid.UUID, alert_id: uuid.UUID) -> CaregiverAlert:
    try:
        return CaregiverAlert.objects.get(pk=alert_id, elder_id=elder_id)
    except CaregiverAlert.DoesNotExist as exc:
        raise AlertNotFoundError("Alert not found.") from exc
