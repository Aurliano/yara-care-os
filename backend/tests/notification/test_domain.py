import uuid

import pytest

from domains.notification.enums import AlertSeverity
from domains.notification.exceptions import AlertNotFoundError
from domains.notification.models import CaregiverAlert
from domains.notification.services.alerts import get_alert, list_elder_alerts, record_caregiver_alert


@pytest.mark.django_db
def test_record_alert_is_idempotent(elder):
    first = record_caregiver_alert(
        elder_id=elder.id,
        title="داروی صبح هنوز مصرف نشده",
        body="یادآوری پاسخ داده نشد.",
        severity=AlertSeverity.ATTENTION,
        source_type="NOTIFY_CAREGIVER",
        source_reference="exec-1",
    )
    second = record_caregiver_alert(
        elder_id=elder.id,
        title="different",
        body="different",
        severity=AlertSeverity.URGENT,
        source_type="NOTIFY_CAREGIVER",
        source_reference="exec-1",
    )
    assert first.id == second.id
    assert CaregiverAlert.objects.count() == 1
    assert second.title == "داروی صبح هنوز مصرف نشده"


@pytest.mark.django_db
def test_list_and_get_alert(elder):
    recorded = record_caregiver_alert(
        elder_id=elder.id,
        title="داروی صبح انجام نشد",
        body="این نوبت انجام نشد.",
        severity=AlertSeverity.URGENT,
        source_type="MEDICATION_MISSED",
        source_reference="completion-1",
    )
    items = list_elder_alerts(elder_id=elder.id)
    assert [item.id for item in items] == [recorded.id]
    fetched = get_alert(elder_id=elder.id, alert_id=recorded.id)
    assert fetched.title == recorded.title
    with pytest.raises(AlertNotFoundError):
        get_alert(elder_id=elder.id, alert_id=uuid.uuid4())
