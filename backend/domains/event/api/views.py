"""Read-only Event query API views."""

import uuid

from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from domains.event.api.serializers import EventRecordSerializer
from domains.event.models import EventRecord
from domains.event.services.queries import (
    MAX_EVENT_QUERY_LIMIT,
    get_events_by_correlation,
    get_events_by_producer,
    get_events_since,
)


class EventRecordListView(APIView):
    """Operational read queries for trace and debug."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        correlation_id = request.query_params.get("correlation_id")
        producer = request.query_params.get("producer")
        since = request.query_params.get("since")
        try:
            limit = int(request.query_params.get("limit", 100))
        except (TypeError, ValueError):
            return Response({"detail": "Invalid limit."}, status=status.HTTP_400_BAD_REQUEST)
        if limit < 1 or limit > MAX_EVENT_QUERY_LIMIT:
            return Response(
                {"detail": f"limit must be between 1 and {MAX_EVENT_QUERY_LIMIT}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if correlation_id:
            events = get_events_by_correlation(correlation_id, limit=limit)
        elif producer:
            events = get_events_by_producer(producer, limit=limit)
        elif since:
            parsed = parse_datetime(since)
            if parsed is None:
                return Response({"detail": "Invalid since timestamp."}, status=status.HTTP_400_BAD_REQUEST)
            events = get_events_since(since=parsed, limit=limit)
        else:
            return Response(
                {"detail": "Provide one of: correlation_id, producer, since."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(EventRecordSerializer(events, many=True).data)


class EventDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, event_id: uuid.UUID) -> Response:
        event = get_object_or_404(EventRecord, pk=event_id)
        return Response(EventRecordSerializer(event).data)
