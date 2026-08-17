"""Communication transport join APIs. Clients never talk to the vendor."""

from __future__ import annotations

import uuid

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api.errors import domain_error_response
from domains.communication.exceptions import (
    AuthorizationDeniedError,
    CallAttemptNotFoundError,
    CommunicationError,
    CommunicationProviderError,
    ContactNotFoundError,
    EntitlementDeniedError,
    InvalidSessionStateError,
    SessionNotFoundError,
)
from domains.communication.services.sessions import get_session
from domains.identity_access.enums import PermissionCode
from domains.identity_access.models import Elder
from domains.identity_access.services.authorization import can, user_is_associated_with_elder
from infrastructure.communication.api.serializers import (
    EndCallSerializer,
    LoginUrlSerializer,
    StartCallSerializer,
)
from infrastructure.communication.models import ProviderSubjectType
from infrastructure.communication.services import end_call, issue_login_url, start_call


def _error_response(exc: CommunicationError) -> Response:
    if isinstance(exc, CommunicationProviderError):
        return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
    return domain_error_response(
        exc,
        base_type=CommunicationError,
        not_found=(ContactNotFoundError, SessionNotFoundError, CallAttemptNotFoundError),
        conflict=(InvalidSessionStateError,),
        forbidden=(AuthorizationDeniedError, EntitlementDeniedError),
    )


def _require_permission(user, permission_code: str, elder: Elder) -> None:
    if not can(user, permission_code, elder):
        raise AuthorizationDeniedError(f"Permission {permission_code} is required.")


def _require_membership(user, elder: Elder) -> None:
    if not user_is_associated_with_elder(user, elder):
        raise AuthorizationDeniedError("Active membership is required.")


def _caller_subject(request: Request, elder_id: uuid.UUID) -> tuple[str, uuid.UUID]:
    replica_header = request.headers.get("X-Replica-ID")
    if replica_header:
        return ProviderSubjectType.ELDER_HUB, elder_id
    return ProviderSubjectType.USER, request.user.id


def _display_name(request: Request, subject_type: str, elder: Elder) -> str:
    if subject_type == ProviderSubjectType.ELDER_HUB:
        return elder.full_name or "Hub"
    return getattr(request.user, "full_name", "") or "Caregiver"


def _join_payload(result) -> dict:
    payload = {
        "joinToken": result.join_token,
        "expiresAt": result.expires_at.isoformat().replace("+00:00", "Z"),
    }
    if result.session_id is not None:
        payload["sessionId"] = str(result.session_id)
    return payload


class CallStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = StartCallSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        elder = get_object_or_404(Elder, pk=data["elder_id"])
        try:
            _require_membership(request.user, elder)
            _require_permission(request.user, PermissionCode.INITIATE_CALL, elder)
            subject_type, subject_id = _caller_subject(request, elder.id)
            result = start_call(
                elder_id=elder.id,
                channel=data["channel"],
                recipient_contact_id=data["recipient_contact_id"],
                initiator_user_id=request.user.id,
                subject_type=subject_type,
                subject_id=subject_id,
                room_title=elder.full_name or "Yara",
                user_display_name=_display_name(request, subject_type, elder),
            )
        except CommunicationError as exc:
            return _error_response(exc)
        return Response(_join_payload(result), status=status.HTTP_201_CREATED)


class CallEndView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = EndCallSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session_id = serializer.validated_data["session_id"]
        try:
            session = get_session(session_id)
            elder = get_object_or_404(Elder, pk=session.elder_id)
            _require_membership(request.user, elder)
            end_call(session_id=session_id)
        except CommunicationError as exc:
            return _error_response(exc)
        return Response({"status": "ended"})


class LoginUrlView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = LoginUrlSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        elder = get_object_or_404(Elder, pk=serializer.validated_data["elder_id"])
        try:
            _require_membership(request.user, elder)
            _require_permission(request.user, PermissionCode.INITIATE_CALL, elder)
            subject_type, subject_id = _caller_subject(request, elder.id)
            result = issue_login_url(
                elder_id=elder.id,
                subject_type=subject_type,
                subject_id=subject_id,
                room_title=elder.full_name or "Yara",
                user_display_name=_display_name(request, subject_type, elder),
            )
        except CommunicationError as exc:
            return _error_response(exc)
        return Response(_join_payload(result))
