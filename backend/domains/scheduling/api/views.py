"""Scheduling management and query API."""

import uuid

from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api.errors import domain_error_response
from domains.scheduling.api.serializers import (
    OccurrenceSerializer,
    ScheduleCreateSerializer,
    ScheduleDefinitionSerializer,
    ScheduleExceptionCreateSerializer,
    ScheduleExceptionSerializer,
    ScheduleUpdateSerializer,
)
from domains.scheduling.exceptions import (
    InvalidOccurrenceStateError,
    InvalidScheduleStateError,
    OccurrenceNotFoundError,
    RescheduleCollisionError,
    ScheduleNotFoundError,
    SchedulingError,
)
from domains.scheduling.models import ScheduleDefinition
from domains.scheduling.services.occurrences import (
    cancel_occurrence,
    get_next_occurrence,
    get_occurrence,
    get_occurrences_between,
    get_upcoming_occurrences,
    skip_occurrence,
)
from domains.scheduling.services.schedules import (
    add_schedule_exception,
    cancel_schedule,
    create_schedule,
    get_schedule,
    pause_schedule,
    resume_schedule,
    update_schedule,
)


def _scheduling_error_response(exc: SchedulingError) -> Response:
    return domain_error_response(
        exc,
        base_type=SchedulingError,
        not_found=(ScheduleNotFoundError, OccurrenceNotFoundError),
        conflict=(InvalidScheduleStateError, InvalidOccurrenceStateError, RescheduleCollisionError),
    )


class ScheduleListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = ScheduleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            schedule = create_schedule(
                owner_reference=data["owner_reference"],
                recurrence_definition=data["recurrence_definition"],
                timezone_name=data["timezone"],
                start_at=data["start_at"],
                end_at=data.get("end_at"),
            )
        except SchedulingError as exc:
            return _scheduling_error_response(exc)
        return Response(ScheduleDefinitionSerializer(schedule).data, status=status.HTTP_201_CREATED)


class ScheduleDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, schedule_id: uuid.UUID) -> Response:
        try:
            schedule = get_schedule(schedule_id)
        except SchedulingError as exc:
            return _scheduling_error_response(exc)
        return Response(ScheduleDefinitionSerializer(schedule).data)

    def patch(self, request: Request, schedule_id: uuid.UUID) -> Response:
        serializer = ScheduleUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        update_kwargs = dict(serializer.validated_data)
        if "timezone" in update_kwargs:
            update_kwargs["timezone_name"] = update_kwargs.pop("timezone")
        try:
            schedule = update_schedule(schedule_id, **update_kwargs)
        except SchedulingError as exc:
            return _scheduling_error_response(exc)
        return Response(ScheduleDefinitionSerializer(schedule).data)


class SchedulePauseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, schedule_id: uuid.UUID) -> Response:
        try:
            schedule = pause_schedule(schedule_id)
        except SchedulingError as exc:
            return _scheduling_error_response(exc)
        return Response(ScheduleDefinitionSerializer(schedule).data)


class ScheduleResumeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, schedule_id: uuid.UUID) -> Response:
        try:
            schedule = resume_schedule(schedule_id)
        except SchedulingError as exc:
            return _scheduling_error_response(exc)
        return Response(ScheduleDefinitionSerializer(schedule).data)


class ScheduleCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, schedule_id: uuid.UUID) -> Response:
        try:
            schedule = cancel_schedule(schedule_id)
        except SchedulingError as exc:
            return _scheduling_error_response(exc)
        return Response(ScheduleDefinitionSerializer(schedule).data)


class ScheduleExceptionCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, schedule_id: uuid.UUID) -> Response:
        serializer = ScheduleExceptionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            exception = add_schedule_exception(
                schedule_id,
                original_time=data["original_time"],
                exception_type=data["exception_type"],
                replacement_time=data.get("replacement_time"),
                reason=data.get("reason", ""),
            )
        except SchedulingError as exc:
            return _scheduling_error_response(exc)
        return Response(ScheduleExceptionSerializer(exception).data, status=status.HTTP_201_CREATED)


class OccurrenceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, occurrence_id: uuid.UUID) -> Response:
        try:
            occurrence = get_occurrence(occurrence_id)
        except SchedulingError as exc:
            return _scheduling_error_response(exc)
        return Response(OccurrenceSerializer(occurrence).data)


class ScheduleOccurrenceQueryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, schedule_id: uuid.UUID) -> Response:
        get_object_or_404(ScheduleDefinition, pk=schedule_id)
        query_type = request.query_params.get("type", "upcoming")

        if query_type == "next":
            after = request.query_params.get("after")
            parsed_after = parse_datetime(after) if after else None
            occurrence = get_next_occurrence(schedule_definition_id=schedule_id, after=parsed_after)
            if occurrence is None:
                return Response(status=status.HTTP_404_NOT_FOUND)
            return Response(OccurrenceSerializer(occurrence).data)

        if query_type == "between":
            start = parse_datetime(request.query_params.get("start", ""))
            end = parse_datetime(request.query_params.get("end", ""))
            if start is None or end is None:
                return Response({"detail": "start and end are required."}, status=status.HTTP_400_BAD_REQUEST)
            occurrences = get_occurrences_between(
                schedule_definition_id=schedule_id,
                start=start,
                end=end,
            )
            return Response(OccurrenceSerializer(occurrences, many=True).data)

        limit = int(request.query_params.get("limit", 10))
        after = request.query_params.get("after")
        parsed_after = parse_datetime(after) if after else None
        occurrences = get_upcoming_occurrences(
            schedule_definition_id=schedule_id,
            limit=limit,
            after=parsed_after,
        )
        return Response(OccurrenceSerializer(occurrences, many=True).data)


class OccurrenceSkipView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, occurrence_id: uuid.UUID) -> Response:
        try:
            occurrence = skip_occurrence(occurrence_id=occurrence_id)
        except SchedulingError as exc:
            return _scheduling_error_response(exc)
        return Response(OccurrenceSerializer(occurrence).data)


class OccurrenceCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, occurrence_id: uuid.UUID) -> Response:
        try:
            occurrence = cancel_occurrence(occurrence_id=occurrence_id)
        except SchedulingError as exc:
            return _scheduling_error_response(exc)
        return Response(OccurrenceSerializer(occurrence).data)
