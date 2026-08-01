"""Care API views."""

import uuid

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api.errors import domain_error_response
from domains.care.api.serializers import (
    CareActivityCreateSerializer,
    CareActivitySerializer,
    CareActivityUpdateSerializer,
    CareCompletionSerializer,
    InterpretExecutionResultSerializer,
    PrescriptionCreateSerializer,
    PrescriptionSerializer,
    PrescriptionUpdateSerializer,
)
from domains.care.exceptions import (
    CareActivityNotFoundError,
    CareError,
    ElderNotFoundError,
    InvalidCareActivityStateError,
    InvalidExecutionResultError,
    PrescriptionNotFoundError,
)
from domains.care.services.activities import (
    create_care_activity,
    end_care_activity,
    get_care_activity,
    get_care_activity_status,
    get_elder_care_activities,
    pause_care_activity,
    resume_care_activity,
    update_care_activity,
)
from domains.care.services.interpretation import get_care_completion_history, interpret_execution_result
from domains.care.services.prescriptions import create_prescription, get_active_prescriptions, get_prescription, update_prescription
from domains.identity_access.api.permissions import HasElderAccess
from domains.identity_access.models import Elder
from domains.identity_access.services.authorization import can


def _care_error_response(exc: CareError) -> Response:
    return domain_error_response(
        exc,
        base_type=CareError,
        not_found=(CareActivityNotFoundError, PrescriptionNotFoundError, ElderNotFoundError),
        conflict=(InvalidCareActivityStateError, InvalidExecutionResultError),
    )


class ElderCareActivityListCreateView(APIView):
    permission_classes = [IsAuthenticated, HasElderAccess]

    def get(self, request: Request, elder_id: uuid.UUID) -> Response:
        elder = get_object_or_404(Elder, pk=elder_id)
        if not can(request.user, "VIEW_ELDER_STATUS", elder):
            return Response(status=status.HTTP_403_FORBIDDEN)
        activities = get_elder_care_activities(elder_id=elder_id)
        return Response(CareActivitySerializer(activities, many=True).data)

    def post(self, request: Request, elder_id: uuid.UUID) -> Response:
        elder = get_object_or_404(Elder, pk=elder_id)
        if not can(request.user, "MANAGE_MEDICATION", elder):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = CareActivityCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            activity = create_care_activity(elder_id=elder_id, **serializer.validated_data)
        except CareError as exc:
            return _care_error_response(exc)
        return Response(CareActivitySerializer(activity).data, status=status.HTTP_201_CREATED)


class CareActivityDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, care_activity_id: uuid.UUID) -> Response:
        try:
            activity = get_care_activity(care_activity_id)
        except CareActivityNotFoundError as exc:
            return _care_error_response(exc)
        return Response(CareActivitySerializer(activity).data)

    def patch(self, request: Request, care_activity_id: uuid.UUID) -> Response:
        serializer = CareActivityUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            activity = update_care_activity(care_activity_id, **serializer.validated_data)
        except CareError as exc:
            return _care_error_response(exc)
        return Response(CareActivitySerializer(activity).data)


class CareActivityStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, care_activity_id: uuid.UUID) -> Response:
        try:
            return Response(get_care_activity_status(care_activity_id))
        except CareActivityNotFoundError as exc:
            return _care_error_response(exc)


class CareActivityPauseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, care_activity_id: uuid.UUID) -> Response:
        try:
            activity = pause_care_activity(care_activity_id=care_activity_id)
        except CareError as exc:
            return _care_error_response(exc)
        return Response(CareActivitySerializer(activity).data)


class CareActivityResumeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, care_activity_id: uuid.UUID) -> Response:
        try:
            activity = resume_care_activity(care_activity_id=care_activity_id)
        except CareError as exc:
            return _care_error_response(exc)
        return Response(CareActivitySerializer(activity).data)


class CareActivityEndView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, care_activity_id: uuid.UUID) -> Response:
        try:
            activity = end_care_activity(care_activity_id=care_activity_id)
        except CareError as exc:
            return _care_error_response(exc)
        return Response(CareActivitySerializer(activity).data)


class CareActivityCompletionHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, care_activity_id: uuid.UUID) -> Response:
        try:
            get_care_activity(care_activity_id)
        except CareActivityNotFoundError as exc:
            return _care_error_response(exc)
        history = get_care_completion_history(care_activity_id=care_activity_id)
        return Response(CareCompletionSerializer(history, many=True).data)


class ElderPrescriptionListCreateView(APIView):
    permission_classes = [IsAuthenticated, HasElderAccess]

    def get(self, request: Request, elder_id: uuid.UUID) -> Response:
        elder = get_object_or_404(Elder, pk=elder_id)
        if not can(request.user, "VIEW_ELDER_STATUS", elder):
            return Response(status=status.HTTP_403_FORBIDDEN)
        prescriptions = get_active_prescriptions(elder_id=elder_id)
        return Response(PrescriptionSerializer(prescriptions, many=True).data)

    def post(self, request: Request, elder_id: uuid.UUID) -> Response:
        elder = get_object_or_404(Elder, pk=elder_id)
        if not can(request.user, "MANAGE_MEDICATION", elder):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = PrescriptionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            prescription = create_prescription(elder_id=elder_id, **serializer.validated_data)
        except CareError as exc:
            return _care_error_response(exc)
        return Response(PrescriptionSerializer(prescription).data, status=status.HTTP_201_CREATED)


class PrescriptionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, prescription_id: uuid.UUID) -> Response:
        try:
            prescription = get_prescription(prescription_id)
        except PrescriptionNotFoundError as exc:
            return _care_error_response(exc)
        return Response(PrescriptionSerializer(prescription).data)

    def patch(self, request: Request, prescription_id: uuid.UUID) -> Response:
        serializer = PrescriptionUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            prescription = update_prescription(prescription_id, **serializer.validated_data)
        except CareError as exc:
            return _care_error_response(exc)
        return Response(PrescriptionSerializer(prescription).data)


class InterpretExecutionResultView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = InterpretExecutionResultSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            completion = interpret_execution_result(**serializer.validated_data)
        except CareError as exc:
            return _care_error_response(exc)
        return Response(CareCompletionSerializer(completion).data, status=status.HTTP_201_CREATED)
