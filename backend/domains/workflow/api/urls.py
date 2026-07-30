"""Workflow API routes."""

from django.urls import path

from domains.workflow.api.views import (
    ActiveExecutionsView,
    AdvanceEscalationView,
    CancelExecutionView,
    ExecutionDetailView,
    ExecutionStatusView,
    PostponeExecutionView,
    ReportActionResultView,
    SubmitEvidenceView,
    WorkflowDefinitionByCodeView,
    WorkflowDefinitionDetailView,
)

urlpatterns = [
    path("workflow-definitions/<uuid:definition_id>/", WorkflowDefinitionDetailView.as_view(), name="workflow-definition-detail"),
    path("workflow-definitions/by-code/<str:code>/", WorkflowDefinitionByCodeView.as_view(), name="workflow-definition-by-code"),
    path("executions/active/", ActiveExecutionsView.as_view(), name="workflow-executions-active"),
    path("executions/<uuid:execution_id>/", ExecutionDetailView.as_view(), name="workflow-execution-detail"),
    path("executions/<uuid:execution_id>/status/", ExecutionStatusView.as_view(), name="workflow-execution-status"),
    path("executions/<uuid:execution_id>/evidence/", SubmitEvidenceView.as_view(), name="workflow-execution-evidence"),
    path("executions/<uuid:execution_id>/postpone/", PostponeExecutionView.as_view(), name="workflow-execution-postpone"),
    path("executions/<uuid:execution_id>/cancel/", CancelExecutionView.as_view(), name="workflow-execution-cancel"),
    path("executions/<uuid:execution_id>/escalate/", AdvanceEscalationView.as_view(), name="workflow-execution-escalate"),
    path("executions/<uuid:execution_id>/action-results/", ReportActionResultView.as_view(), name="workflow-execution-action-result"),
]
