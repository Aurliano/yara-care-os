"""Communication API views."""

import uuid

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api.errors import domain_error_response
from domains.communication.api.serializers import (
    CallAttemptSerializer,
    CommunicationSessionSerializer,
    ContactCreateSerializer,
    ContactSerializer,
    ContactUpdateSerializer,
    InitiateSessionSerializer,
    ReportAttemptResultSerializer,
    SessionParticipantSerializer,
)
from domains.communication.exceptions import (
    AuthorizationDeniedError,
    CallAttemptNotFoundError,
    CommunicationError,
    ContactNotFoundError,
    EntitlementDeniedError,
    InvalidSessionStateError,
    SessionNotFoundError,
)
from domains.communication.services.contacts import (
    archive_contact,
    create_contact,
    get_contact,
    get_elder_contacts,
    get_priority_contacts,
    remove_priority_contact,
    set_priority_contact,
    update_contact,
)
from domains.communication.services.sessions import (
    accept_session,
    cancel_session,
    decline_session,
    end_session,
    get_call_attempts,
    get_recent_sessions,
    get_session,
    get_session_participants,
    initiate_session,
    record_call_attempt,
    report_attempt_result,
)
from domains.identity_access.api.permissions import HasElderAccess
from domains.identity_access.enums import PermissionCode
from domains.identity_access.models import Elder
from domains.identity_access.services.authorization import can


def _communication_error_response(exc: CommunicationError) -> Response:
    return domain_error_response(
        exc,
        base_type=CommunicationError,
        not_found=(ContactNotFoundError, SessionNotFoundError, CallAttemptNotFoundError),
        conflict=(InvalidSessionStateError, EntitlementDeniedError),
        forbidden=(AuthorizationDeniedError,),
    )


def _require_permission(user, permission_code: str, elder: Elder) -> None:
    if not can(user, permission_code, elder):
        raise AuthorizationDeniedError(f"Permission {permission_code} is required.")


class ElderContactListCreateView(APIView):
    permission_classes = [IsAuthenticated, HasElderAccess]

    def get(self, request: Request, elder_id: uuid.UUID) -> Response:
        elder = get_object_or_404(Elder, pk=elder_id)
        _require_permission(request.user, PermissionCode.VIEW_ELDER_STATUS, elder)
        contacts = get_elder_contacts(elder_id=elder_id)
        return Response(ContactSerializer(contacts, many=True).data)

    def post(self, request: Request, elder_id: uuid.UUID) -> Response:
        elder = get_object_or_404(Elder, pk=elder_id)
        _require_permission(request.user, PermissionCode.MANAGE_CONTACTS, elder)
        serializer = ContactCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            contact = create_contact(elder_id=elder_id, **serializer.validated_data)
        except CommunicationError as exc:
            return _communication_error_response(exc)
        return Response(ContactSerializer(contact).data, status=status.HTTP_201_CREATED)


class ContactDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, contact_id: uuid.UUID) -> Response:
        try:
            contact = get_contact(contact_id)
        except ContactNotFoundError as exc:
            return _communication_error_response(exc)
        return Response(ContactSerializer(contact).data)

    def patch(self, request: Request, contact_id: uuid.UUID) -> Response:
        contact = get_contact(contact_id)
        elder = get_object_or_404(Elder, pk=contact.elder_id)
        _require_permission(request.user, PermissionCode.MANAGE_CONTACTS, elder)
        serializer = ContactUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            updated = update_contact(contact_id, **serializer.validated_data)
        except CommunicationError as exc:
            return _communication_error_response(exc)
        return Response(ContactSerializer(updated).data)


class ContactArchiveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, contact_id: uuid.UUID) -> Response:
        contact = get_contact(contact_id)
        elder = get_object_or_404(Elder, pk=contact.elder_id)
        _require_permission(request.user, PermissionCode.MANAGE_CONTACTS, elder)
        try:
            archived = archive_contact(contact_id=contact_id)
        except CommunicationError as exc:
            return _communication_error_response(exc)
        return Response(ContactSerializer(archived).data)


class ContactPriorityView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, contact_id: uuid.UUID) -> Response:
        contact = get_contact(contact_id)
        elder = get_object_or_404(Elder, pk=contact.elder_id)
        _require_permission(request.user, PermissionCode.MANAGE_CONTACTS, elder)
        try:
            updated = set_priority_contact(contact_id=contact_id)
        except CommunicationError as exc:
            return _communication_error_response(exc)
        return Response(ContactSerializer(updated).data)

    def delete(self, request: Request, contact_id: uuid.UUID) -> Response:
        contact = get_contact(contact_id)
        elder = get_object_or_404(Elder, pk=contact.elder_id)
        _require_permission(request.user, PermissionCode.MANAGE_CONTACTS, elder)
        try:
            updated = remove_priority_contact(contact_id=contact_id)
        except CommunicationError as exc:
            return _communication_error_response(exc)
        return Response(ContactSerializer(updated).data)


class ElderPriorityContactsView(APIView):
    permission_classes = [IsAuthenticated, HasElderAccess]

    def get(self, request: Request, elder_id: uuid.UUID) -> Response:
        elder = get_object_or_404(Elder, pk=elder_id)
        _require_permission(request.user, PermissionCode.VIEW_ELDER_STATUS, elder)
        contacts = get_priority_contacts(elder_id=elder_id)
        return Response(ContactSerializer(contacts, many=True).data)


class ElderSessionListCreateView(APIView):
    permission_classes = [IsAuthenticated, HasElderAccess]

    def get(self, request: Request, elder_id: uuid.UUID) -> Response:
        elder = get_object_or_404(Elder, pk=elder_id)
        _require_permission(request.user, PermissionCode.VIEW_ELDER_STATUS, elder)
        sessions = get_recent_sessions(elder_id=elder_id)
        return Response(CommunicationSessionSerializer(sessions, many=True).data)

    def post(self, request: Request, elder_id: uuid.UUID) -> Response:
        elder = get_object_or_404(Elder, pk=elder_id)
        _require_permission(request.user, PermissionCode.INITIATE_CALL, elder)
        serializer = InitiateSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if data.get("initiator_user_id") is None and data.get("initiator_contact_id") is None:
            data["initiator_user_id"] = request.user.id
        try:
            session = initiate_session(elder_id=elder_id, **data)
        except CommunicationError as exc:
            return _communication_error_response(exc)
        return Response(CommunicationSessionSerializer(session).data, status=status.HTTP_201_CREATED)


class SessionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, session_id: uuid.UUID) -> Response:
        try:
            session = get_session(session_id)
        except SessionNotFoundError as exc:
            return _communication_error_response(exc)
        return Response(CommunicationSessionSerializer(session).data)


class SessionParticipantsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, session_id: uuid.UUID) -> Response:
        try:
            get_session(session_id)
        except SessionNotFoundError as exc:
            return _communication_error_response(exc)
        participants = get_session_participants(session_id=session_id)
        return Response(SessionParticipantSerializer(participants, many=True).data)


class SessionCallAttemptsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, session_id: uuid.UUID) -> Response:
        try:
            get_session(session_id)
        except SessionNotFoundError as exc:
            return _communication_error_response(exc)
        attempts = get_call_attempts(session_id=session_id)
        return Response(CallAttemptSerializer(attempts, many=True).data)

    def post(self, request: Request, session_id: uuid.UUID) -> Response:
        try:
            get_session(session_id)
        except SessionNotFoundError as exc:
            return _communication_error_response(exc)
        try:
            attempt = record_call_attempt(session_id=session_id)
        except CommunicationError as exc:
            return _communication_error_response(exc)
        return Response(CallAttemptSerializer(attempt).data, status=status.HTTP_201_CREATED)


class SessionAcceptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, session_id: uuid.UUID) -> Response:
        try:
            session = accept_session(session_id=session_id)
        except CommunicationError as exc:
            return _communication_error_response(exc)
        return Response(CommunicationSessionSerializer(session).data)


class SessionDeclineView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, session_id: uuid.UUID) -> Response:
        try:
            session = decline_session(session_id=session_id)
        except CommunicationError as exc:
            return _communication_error_response(exc)
        return Response(CommunicationSessionSerializer(session).data)


class SessionCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, session_id: uuid.UUID) -> Response:
        try:
            session = cancel_session(session_id=session_id)
        except CommunicationError as exc:
            return _communication_error_response(exc)
        return Response(CommunicationSessionSerializer(session).data)


class SessionEndView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, session_id: uuid.UUID) -> Response:
        try:
            session = end_session(session_id=session_id)
        except CommunicationError as exc:
            return _communication_error_response(exc)
        return Response(CommunicationSessionSerializer(session).data)


class CallAttemptResultView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, attempt_id: uuid.UUID) -> Response:
        serializer = ReportAttemptResultSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            attempt = report_attempt_result(attempt_id=attempt_id, **serializer.validated_data)
        except CommunicationError as exc:
            return _communication_error_response(exc)
        return Response(CallAttemptSerializer(attempt).data)
