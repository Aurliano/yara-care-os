import pytest

from domains.identity_access.services.profiles import create_user
from domains.notification.enums import AlertSeverity
from domains.notification.services.alerts import record_caregiver_alert


@pytest.mark.django_db
def test_list_alerts_api(authenticated_client, elder):
    recorded = record_caregiver_alert(
        elder_id=elder.id,
        title="داروی صبح هنوز مصرف نشده",
        body="یادآوری پاسخ داده نشد.",
        severity=AlertSeverity.ATTENTION,
        source_type="NOTIFY_CAREGIVER",
        source_reference="exec-api-1",
    )
    response = authenticated_client.get(f"/api/v1/elders/{elder.id}/alerts/")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == str(recorded.id)
    assert payload[0]["severity"] == "attention"
    assert payload[0]["occurred_at"]
    assert "source_type" not in payload[0]


@pytest.mark.django_db
def test_alert_detail_api(authenticated_client, elder):
    recorded = record_caregiver_alert(
        elder_id=elder.id,
        title="داروی صبح انجام نشد",
        body="این نوبت انجام نشد.",
        severity=AlertSeverity.URGENT,
        source_type="MEDICATION_MISSED",
        source_reference="completion-api-1",
    )
    response = authenticated_client.get(f"/api/v1/elders/{elder.id}/alerts/{recorded.id}/")
    assert response.status_code == 200
    assert response.json()["title"] == recorded.title


@pytest.mark.django_db
def test_alerts_require_membership(api_client, elder):
    other = create_user(
        phone="+989135555555",
        password="securepass123",
        full_name="Outsider",
    )
    api_client.force_authenticate(user=other)
    response = api_client.get(f"/api/v1/elders/{elder.id}/alerts/")
    assert response.status_code == 403
