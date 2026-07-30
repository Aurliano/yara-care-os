import pytest

from domains.workflow.enums import EvidenceSourceType
from tests.workflow.conftest import start_due_execution


@pytest.mark.django_db
def test_submit_evidence_api(authenticated_client, due_occurrence, workflow_definition):
    execution = start_due_execution(due_occurrence, workflow_definition)
    response = authenticated_client.post(
        f"/api/v1/executions/{execution.id}/evidence/",
        {
            "evidence_type": "HUB_CONFIRMATION",
            "source_type": EvidenceSourceType.DIRECT_INTERACTION,
            "source_reference": "api-evidence-1",
        },
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["status"] == "CONFIRMED"


@pytest.mark.django_db
def test_internal_timeout_endpoint_not_exposed(authenticated_client, due_occurrence, workflow_definition):
    execution = start_due_execution(due_occurrence, workflow_definition)
    response = authenticated_client.post(f"/api/v1/executions/{execution.id}/timeout/")
    assert response.status_code == 404
