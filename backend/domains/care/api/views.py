import time
import uuid
from typing import Any

from django.core.cache import cache
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api.errors import domain_error_response
from domains.care.models import CareActivity, Prescription
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
from domains.care.services.prescriptions import (
    create_prescription,
    get_active_prescriptions,
    get_history_prescriptions,
    get_prescription,
    update_prescription,
)
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


def _extract_idempotency_key(request: Request) -> str:
    return (
        request.headers.get("Idempotency-Key")
        or request.headers.get("idempotency-key")
        or request.META.get("HTTP_IDEMPOTENCY_KEY")
        or ""
    ).strip()


def _coordinate_idempotency(cache_key: str, lock_key: str, max_wait: float = 3.0) -> tuple[bool, Any]:
    """Atomically coordinate concurrent requests with the same idempotency key.

    Returns (is_locked, cached_result).
    """
    cached = cache.get(cache_key)
    if cached is not None:
        return False, cached

    deadline = time.monotonic() + max_wait
    while time.monotonic() < deadline:
        if cache.add(lock_key, "1", timeout=15):
            cached = cache.get(cache_key)
            if cached is not None:
                cache.delete(lock_key)
                return False, cached
            return True, None
        time.sleep(0.05)
        cached = cache.get(cache_key)
        if cached is not None:
            return False, cached

    if cache.add(lock_key, "1", timeout=15):
        return True, None
    return False, None


class ElderCareActivityListCreateView(APIView):
    permission_classes = [IsAuthenticated, HasElderAccess]

    def get(self, request: Request, elder_id: uuid.UUID) -> Response:
        elder = get_object_or_404(Elder, pk=elder_id)
        if not can(request.user, "VIEW_ELDER_STATUS", elder):
            return Response(status=status.HTTP_403_FORBIDDEN)
        status_param = request.query_params.get("status")
        activities = get_elder_care_activities(elder_id=elder_id, status=status_param)
        return Response(CareActivitySerializer(activities, many=True).data)

    def post(self, request: Request, elder_id: uuid.UUID) -> Response:
        elder = get_object_or_404(Elder, pk=elder_id)
        if not can(request.user, "MANAGE_MEDICATION", elder):
            return Response(status=status.HTTP_403_FORBIDDEN)

        idempotency_key = _extract_idempotency_key(request)
        cache_key = f"idempotency:care_activity:{elder_id}:{idempotency_key}" if idempotency_key else None
        lock_key = f"lock:{cache_key}" if cache_key else None
        acquired_lock = False

        if cache_key and lock_key:
            acquired_lock, cached_data = _coordinate_idempotency(cache_key, lock_key)
            if cached_data is not None:
                return Response(cached_data, status=status.HTTP_201_CREATED)

        try:
            serializer = CareActivityCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            if idempotency_key:
                confirmation_req = dict(validated_data.get("confirmation_requirement") or {})
                confirmation_req["idempotency_key"] = idempotency_key
                validated_data["confirmation_requirement"] = confirmation_req

            with transaction.atomic():
                Elder.objects.select_for_update().get(pk=elder_id)
                if idempotency_key:
                    existing_activity = CareActivity.objects.filter(
                        elder_id=elder_id,
                        confirmation_requirement__idempotency_key=idempotency_key,
                    ).first()
                    if existing_activity is not None:
                        data = CareActivitySerializer(existing_activity).data
                        if cache_key:
                            cache.set(cache_key, data, timeout=300)
                        return Response(data, status=status.HTTP_201_CREATED)

                activity = create_care_activity(elder_id=elder_id, **validated_data)

            data = CareActivitySerializer(activity).data
            if cache_key:
                cache.set(cache_key, data, timeout=300)
            return Response(data, status=status.HTTP_201_CREATED)
        except CareError as exc:
            return _care_error_response(exc)
        finally:
            if lock_key and acquired_lock:
                cache.delete(lock_key)



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
        status_param = request.query_params.get("status")
        if status_param == "history" or status_param in {CareActivityStatus.ENDED, CareActivityStatus.CANCELLED}:
            prescriptions = get_history_prescriptions(elder_id=elder_id)
        else:
            prescriptions = get_active_prescriptions(elder_id=elder_id)
        return Response(PrescriptionSerializer(prescriptions, many=True).data)

    def post(self, request: Request, elder_id: uuid.UUID) -> Response:
        elder = get_object_or_404(Elder, pk=elder_id)
        if not can(request.user, "MANAGE_MEDICATION", elder):
            return Response(status=status.HTTP_403_FORBIDDEN)

        idempotency_key = _extract_idempotency_key(request)
        cache_key = f"idempotency:prescription:{elder_id}:{idempotency_key}" if idempotency_key else None
        lock_key = f"lock:{cache_key}" if cache_key else None
        acquired_lock = False

        if cache_key and lock_key:
            acquired_lock, cached_data = _coordinate_idempotency(cache_key, lock_key)
            if cached_data is not None:
                return Response(cached_data, status=status.HTTP_201_CREATED)

        try:
            serializer = PrescriptionCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            if idempotency_key:
                confirmation_req = dict(validated_data.get("confirmation_requirement") or {})
                confirmation_req["idempotency_key"] = idempotency_key
                validated_data["confirmation_requirement"] = confirmation_req

            with transaction.atomic():
                Elder.objects.select_for_update().get(pk=elder_id)
                if idempotency_key:
                    existing_activity = (
                        CareActivity.objects.filter(
                            elder_id=elder_id,
                            confirmation_requirement__idempotency_key=idempotency_key,
                        )
                        .select_related("prescription")
                        .first()
                    )
                    if existing_activity is not None and hasattr(existing_activity, "prescription"):
                        data = PrescriptionSerializer(existing_activity.prescription).data
                        if cache_key:
                            cache.set(cache_key, data, timeout=300)
                        return Response(data, status=status.HTTP_201_CREATED)

                prescription = create_prescription(elder_id=elder_id, **validated_data)

            data = PrescriptionSerializer(prescription).data
            if cache_key:
                cache.set(cache_key, data, timeout=300)
            return Response(data, status=status.HTTP_201_CREATED)
        except CareError as exc:
            return _care_error_response(exc)
        finally:
            if lock_key and acquired_lock:
                cache.delete(lock_key)



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
