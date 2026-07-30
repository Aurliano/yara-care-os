"""Workflow API views."""

import uuid

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from domains.workflow.api.serializers import (
    ActionResultSubmitSerializer,
    ConfirmationEvidenceSubmitSerializer,
    WorkflowDefinitionSerializer,
    WorkflowExecutionSerializer,
)
from domains.workflow.exceptions import (
    EscalationNotAllowedError,
    InvalidEvidenceError,
    InvalidExecutionStateError,
    PostponeNotAllowedError,
    WorkflowDefinitionConflictError,
    WorkflowError,
)
from domains.workflow.services.actions import advance_escalation, report_action_result
from domains.workflow.services.evidence import submit_confirmation_evidence
from domains.workflow.services.executions import (
    cancel_execution,
    get_active_executions,
    get_execution,
    get_execution_status,
    get_workflow_definition,
    get_workflow_definition_by_code,
)
from domains.workflow.services.postpone import postpone_execution


def _workflow_error_response(exc: WorkflowError) -> Response:
    if isinstance(
        exc,
        (
            InvalidExecutionStateError,
            InvalidEvidenceError,
            PostponeNotAllowedError,
            EscalationNotAllowedError,
            WorkflowDefinitionConflictError,
        ),
    ):
        code = status.HTTP_409_CONFLICT
    else:
        code = status.HTTP_400_BAD_REQUEST
    return Response({"detail": str(exc)}, status=code)


class WorkflowDefinitionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, definition_id: uuid.UUID) -> Response:
        definition = get_workflow_definition(definition_id)
        return Response(WorkflowDefinitionSerializer(definition).data)


class WorkflowDefinitionByCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, code: str) -> Response:
        definition = get_workflow_definition_by_code(code)
        return Response(WorkflowDefinitionSerializer(definition).data)


class ExecutionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, execution_id: uuid.UUID) -> Response:
        execution = get_execution(execution_id)
        return Response(WorkflowExecutionSerializer(execution).data)


class ExecutionStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, execution_id: uuid.UUID) -> Response:
        return Response({"status": get_execution_status(execution_id)})


class ActiveExecutionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        executions = get_active_executions()
        return Response(WorkflowExecutionSerializer(executions, many=True).data)


class SubmitEvidenceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, execution_id: uuid.UUID) -> Response:
        serializer = ConfirmationEvidenceSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            execution = submit_confirmation_evidence(
                execution_id=execution_id,
                evidence_type=data["evidence_type"],
                source_type=data["source_type"],
                source_reference=data["source_reference"],
                actor_user_id=data.get("actor_user_id"),
                payload=data.get("payload") or {},
            )
        except WorkflowError as exc:
            return _workflow_error_response(exc)
        return Response(WorkflowExecutionSerializer(execution).data)


class PostponeExecutionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, execution_id: uuid.UUID) -> Response:
        try:
            execution = postpone_execution(execution_id=execution_id)
        except WorkflowError as exc:
            return _workflow_error_response(exc)
        return Response(WorkflowExecutionSerializer(execution).data)


class CancelExecutionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, execution_id: uuid.UUID) -> Response:
        try:
            execution = cancel_execution(execution_id=execution_id)
        except WorkflowError as exc:
            return _workflow_error_response(exc)
        return Response(WorkflowExecutionSerializer(execution).data)


class AdvanceEscalationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, execution_id: uuid.UUID) -> Response:
        try:
            execution = advance_escalation(execution_id=execution_id)
        except WorkflowError as exc:
            return _workflow_error_response(exc)
        return Response(WorkflowExecutionSerializer(execution).data)


class ReportActionResultView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, execution_id: uuid.UUID) -> Response:
        serializer = ActionResultSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            result = report_action_result(
                execution_id=execution_id,
                action_reference=data["action_reference"],
                action_type=data["action_type"],
                result_status=data["result_status"],
                payload=data.get("payload") or {},
            )
        except WorkflowError as exc:
            return _workflow_error_response(exc)
        return Response(
            {
                "id": str(result.id),
                "action_reference": result.action_reference,
                "result_status": result.result_status,
            }
        )
