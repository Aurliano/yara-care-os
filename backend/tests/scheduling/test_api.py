from datetime import datetime, timedelta

import pytest
from django.utils import timezone
from zoneinfo import ZoneInfo

from domains.scheduling.models import Occurrence
from domains.scheduling.services.schedules import create_schedule
from tests.scheduling.conftest import _aware


@pytest.mark.django_db
def test_create_and_query_schedule_api(authenticated_client):
    import uuid
    from domains.care.enums import CareActivityType
    from domains.care.services.activities import create_care_activity
    from domains.identity_access.services.profiles import create_elder, create_user
    from domains.workflow.services.executions import create_workflow_definition
    from rest_framework.test import APIClient

    user = authenticated_client.handler._force_user
    elder = create_elder(actor=user, full_name="Sched Elder")
    from domains.workflow.medication_reminder_policy import medication_reminder_definition
    wf = create_workflow_definition(
        code=f"wf-sched-{uuid.uuid4().hex[:6]}",
        name="Sched WF",
        definition=medication_reminder_definition(),
    )

    start_at = _aware(datetime(2026, 7, 1, 0, 0, tzinfo=ZoneInfo("UTC")))
    activity = create_care_activity(
        elder_id=elder.id,
        activity_type=CareActivityType.MEDICATION,
        workflow_definition_id=wf.id,
        recurrence_definition={"type": "daily", "times": ["08:00"]},
        timezone_name="Asia/Tehran",
        start_at=start_at,
        display_title="Test Activity",
    )
    schedule_id = activity.schedule_definition_id

    # 1. Authorized user can inspect schedule and occurrences
    detail = authenticated_client.get(f"/api/v1/schedules/{schedule_id}/")
    assert detail.status_code == 200

    occurrences = authenticated_client.get(f"/api/v1/schedules/{schedule_id}/occurrences/")
    assert occurrences.status_code == 200
    occ_list = occurrences.json()
    assert len(occ_list) > 0
    occ_id = occ_list[0]["id"]

    # 2. User B (Outsider) cannot read or mutate User A's schedule or occurrences
    outsider = create_user(
        phone="+989129999999",
        password="securepass123",
        full_name="Outsider User",
    )
    outsider_client = APIClient()
    outsider_client.force_authenticate(user=outsider)

    assert outsider_client.get(f"/api/v1/schedules/{schedule_id}/").status_code == 403
    assert outsider_client.get(f"/api/v1/schedules/{schedule_id}/occurrences/").status_code == 403
    assert outsider_client.post(f"/api/v1/schedules/{schedule_id}/pause/").status_code == 403
    assert outsider_client.post(f"/api/v1/schedules/{schedule_id}/resume/").status_code == 403
    assert outsider_client.post(f"/api/v1/schedules/{schedule_id}/cancel/").status_code == 403

    assert outsider_client.get(f"/api/v1/occurrences/{occ_id}/").status_code == 403
    assert outsider_client.post(f"/api/v1/occurrences/{occ_id}/skip/").status_code == 403
    assert outsider_client.post(f"/api/v1/occurrences/{occ_id}/cancel/").status_code == 403

    # 3. Unauthenticated user receives 401
    unauth = APIClient()
    assert unauth.get(f"/api/v1/schedules/{schedule_id}/").status_code == 401
    assert unauth.get(f"/api/v1/occurrences/{occ_id}/").status_code == 401


@pytest.mark.django_db
def test_due_processing_not_exposed_as_rest_endpoint(authenticated_client):
    import uuid

    response = authenticated_client.post(f"/api/v1/occurrences/{uuid.uuid4()}/due/")
    assert response.status_code == 404

