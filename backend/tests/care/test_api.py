import pytest

from domains.care.enums import CareActivityType


@pytest.mark.django_db
def test_create_care_activity_api(authenticated_client, elder, workflow_definition, recurrence_definition, schedule_start_at):
    response = authenticated_client.post(
        f"/api/v1/elders/{elder.id}/care-activities/",
        {
            "activity_type": CareActivityType.GENERAL,
            "workflow_definition_id": str(workflow_definition.id),
            "recurrence_definition": recurrence_definition,
            "timezone_name": "UTC",
            "start_at": schedule_start_at.isoformat(),
            "display_title": "API activity",
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["display_title"] == "API activity"


@pytest.mark.django_db
def test_create_prescription_api(authenticated_client, elder, workflow_definition, recurrence_definition, schedule_start_at):
    response = authenticated_client.post(
        f"/api/v1/elders/{elder.id}/prescriptions/",
        {
            "workflow_definition_id": str(workflow_definition.id),
            "recurrence_definition": recurrence_definition,
            "timezone_name": "UTC",
            "start_at": schedule_start_at.isoformat(),
            "display_title": "API prescription",
            "medication_reference": "med-api",
            "dosage_information": "1 tablet",
            "elder_friendly_description": "Take your medicine",
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["medication_reference"] == "med-api"


@pytest.mark.django_db
def test_create_prescription_without_workflow_definition_id_auto_defaults(authenticated_client, elder, recurrence_definition, schedule_start_at):
    response = authenticated_client.post(
        f"/api/v1/elders/{elder.id}/prescriptions/",
        {
            "recurrence_definition": recurrence_definition,
            "timezone_name": "UTC",
            "start_at": schedule_start_at.isoformat(),
            "display_title": "Auto Workflow Prescription",
            "medication_reference": "calcium-500",
            "dosage_information": "1 قرص",
            "elder_friendly_description": "بعد از غذا",
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["medication_reference"] == "calcium-500"
    assert response.json()["care_activity"]["workflow_definition_id"] is not None


@pytest.mark.django_db
def test_list_prescriptions_api(authenticated_client, elder):
    response = authenticated_client.get(f"/api/v1/elders/{elder.id}/prescriptions/")
    assert response.status_code == 200
    assert response.json() == []

    response_history = authenticated_client.get(f"/api/v1/elders/{elder.id}/prescriptions/?status=history")
    assert response_history.status_code == 200
    assert response_history.json() == []
