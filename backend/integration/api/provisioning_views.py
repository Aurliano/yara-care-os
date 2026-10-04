"""Hub provisioning API — device registration and authentication."""

from __future__ import annotations

import uuid

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from integration.api.errors import hub_error_response
from integration.exceptions import HubProvisioningError
from integration.services.hub_provisioning import (
    authenticate_hub_device,
    get_hub_provisioning_status,
    register_hub_device,
    revoke_hub_provisioning,
)


class HubProvisionRegisterView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        data = request.data
        serial_number = data.get("serial_number")
        device_model_code = data.get("device_model_code")
        if not serial_number or not device_model_code:
            return Response(
                {"detail": "serial_number and device_model_code are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = register_hub_device(
                serial_number=serial_number,
                device_model_code=device_model_code,
            )
        except Exception as exc:  # noqa: BLE001
            return hub_error_response(exc)
        return Response(result, status=status.HTTP_201_CREATED)


from common.throttling import HubProvisionRateThrottle


class HubProvisionAuthenticateView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]
    throttle_classes = [HubProvisionRateThrottle]

    def post(self, request: Request) -> Response:
        data = request.data
        device_id_raw = data.get("device_id")
        phone = data.get("phone")
        password = data.get("password")
        if not device_id_raw or not phone or not password:
            return Response(
                {"detail": "device_id, phone, and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = authenticate_hub_device(
                device_id=uuid.UUID(device_id_raw),
                phone=phone,
                password=password,
            )
        except HubProvisioningError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as exc:  # noqa: BLE001
            return hub_error_response(exc)
        return Response(result, status=status.HTTP_200_OK)


class HubProvisionStatusView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        device_id_raw = request.query_params.get("device_id") or request.headers.get("X-Device-ID")
        if not device_id_raw:
            return Response(
                {"detail": "device_id query parameter or X-Device-ID header is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = get_hub_provisioning_status(device_id=uuid.UUID(device_id_raw))
        except Exception as exc:  # noqa: BLE001
            return hub_error_response(exc)
        return Response(result, status=status.HTTP_200_OK)


class HubProvisionRevokeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        device_id_raw = request.data.get("device_id") or request.headers.get("X-Device-ID")
        if not device_id_raw:
            return Response(
                {"detail": "device_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            device_id = uuid.UUID(str(device_id_raw))
        except (ValueError, TypeError):
            return Response(
                {"detail": "Invalid device_id format."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from domains.device.services.assignments import get_assignments
        from domains.identity_access.services.authorization import user_is_associated_with_elder
        from domains.device.enums import AssignmentStatus

        assignments = get_assignments(device_id=device_id)
        if assignments:
            assigned = [a for a in assignments if a.status == AssignmentStatus.ASSIGNED]
            elder = assigned[0].elder if assigned else assignments[0].elder
            if not user_is_associated_with_elder(request.user, elder):
                return Response(
                    {"detail": "You do not have permission to revoke provisioning for this device."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        try:
            result = revoke_hub_provisioning(device_id=device_id)
        except Exception as exc:  # noqa: BLE001
            return hub_error_response(exc)
        return Response(result, status=status.HTTP_200_OK)
