"""Notification API views."""

import uuid

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api.errors import domain_error_response
from domains.identity_access.api.permissions import HasElderAccess
from domains.identity_access.models import Elder
from domains.identity_access.services.authorization import can
from domains.notification.api.serializers import CaregiverAlertSerializer
from domains.notification.exceptions import AlertNotFoundError, NotificationError
from domains.notification.services.alerts import get_alert, list_elder_alerts


def _notification_error_response(exc: NotificationError) -> Response:
    return domain_error_response(
        exc,
        base_type=NotificationError,
        not_found=(AlertNotFoundError,),
    )


class ElderAlertListView(APIView):
    permission_classes = [IsAuthenticated, HasElderAccess]

    def get(self, request: Request, elder_id: uuid.UUID) -> Response:
        elder = get_object_or_404(Elder, pk=elder_id)
        if not can(request.user, "VIEW_ELDER_STATUS", elder):
            return Response(status=status.HTTP_403_FORBIDDEN)
        alerts = list_elder_alerts(elder_id=elder_id)
        return Response(CaregiverAlertSerializer(alerts, many=True).data)


class ElderAlertDetailView(APIView):
    permission_classes = [IsAuthenticated, HasElderAccess]

    def get(self, request: Request, elder_id: uuid.UUID, alert_id: uuid.UUID) -> Response:
        elder = get_object_or_404(Elder, pk=elder_id)
        if not can(request.user, "VIEW_ELDER_STATUS", elder):
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            alert = get_alert(elder_id=elder_id, alert_id=alert_id)
        except NotificationError as exc:
            return _notification_error_response(exc)
        return Response(CaregiverAlertSerializer(alert).data)
