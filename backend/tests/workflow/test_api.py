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


@pytest.mark.django_db
def test_workflow_execution_idor_prevented(authenticated_client, due_occurrence, workflow_definition):
    from domains.identity_access.services.profiles import create_user
    from rest_framework.test import APIClient

    execution = start_due_execution(due_occurrence, workflow_definition)

    # 1. Authorized user can inspect execution
    auth_res = authenticated_client.get(f"/api/v1/executions/{execution.id}/")
    assert auth_res.status_code == 200

    # 2. User B (Outsider) cannot inspect, submit evidence, postpone, cancel, or escalate
    outsider = create_user(
        phone="+989127777777",
        password="securepass123",
        full_name="Outsider Workflow User",
    )
    outsider_client = APIClient()
    outsider_client.force_authenticate(user=outsider)

    # Inspect denied
    assert outsider_client.get(f"/api/v1/executions/{execution.id}/").status_code == 403

    # Submit evidence denied
    assert outsider_client.post(
        f"/api/v1/executions/{execution.id}/evidence/",
        {
            "evidence_type": "HUB_CONFIRMATION",
            "source_type": EvidenceSourceType.DIRECT_INTERACTION,
            "source_reference": "outsider-ev",
        },
        format="json",
    ).status_code == 403

    # Postpone denied
    assert outsider_client.post(
        f"/api/v1/executions/{execution.id}/postpone/",
        format="json",
    ).status_code == 403

    # Cancel denied
    assert outsider_client.post(
        f"/api/v1/executions/{execution.id}/cancel/",
        format="json",
    ).status_code == 403

    # Advance escalation denied
    assert outsider_client.post(
        f"/api/v1/executions/{execution.id}/escalate/",
        format="json",
    ).status_code == 403

    # 3. Unauthenticated user receives 401
    unauth = APIClient()
    assert unauth.get(f"/api/v1/executions/{execution.id}/").status_code == 401
    assert unauth.post(f"/api/v1/executions/{execution.id}/evidence/", format="json").status_code == 401

