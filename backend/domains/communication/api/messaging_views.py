"""Views for communication messaging and media attachment APIs."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from django.http import Http404, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api.errors import domain_error_response
from domains.communication.api.messaging_serializers import (
    MessageAttachmentSerializer,
    MessageSerializer,
    SendMessageSerializer,
    UploadMediaSerializer,
)
from domains.communication.exceptions import (
    AttachmentNotFoundError,
    AuthorizationDeniedError,
    CommunicationError,
    InvalidMediaError,
    InvalidMessageError,
    MediaNotFoundError,
    MessageNotFoundError,
)
from domains.communication.models import Message, MessageAttachment
from domains.communication.services.messaging import (
    create_message_attachment,
    get_attachment,
    list_elder_messages,
    mark_message_delivered,
    mark_message_read,
    send_message,
)
from domains.communication.services.storage import open_media_stream
from domains.identity_access.api.permissions import HasElderAccess
from domains.identity_access.enums import PermissionCode
from domains.identity_access.models import Elder
from domains.identity_access.services.authorization import can


def _messaging_error_response(exc: CommunicationError) -> Response:
    return domain_error_response(
        exc,
        base_type=CommunicationError,
        not_found=(MessageNotFoundError, AttachmentNotFoundError, MediaNotFoundError),
        forbidden=(AuthorizationDeniedError,),
    )


class ElderMessagesView(APIView):
    """List or send messages for an Elder."""

    permission_classes = [IsAuthenticated, HasElderAccess]

    def get(self, request: Request, elder_id: uuid.UUID) -> Response:
        elder = get_object_or_404(Elder, id=elder_id)
        if not can(request.user, PermissionCode.VIEW_MESSAGES, elder) and not can(
            request.user, PermissionCode.VIEW_ELDER_STATUS, elder
        ):
            return _messaging_error_response(
                AuthorizationDeniedError("User does not have permission to view messages.")
            )

        since_param = request.query_params.get("since")
        since = None
        if since_param:
            try:
                # Support epoch millis or ISO8601
                if since_param.isdigit():
                    since = datetime.fromtimestamp(int(since_param) / 1000.0, tz=timezone.utc)
                else:
                    clean_param = since_param.replace(" ", "+")
                    parsed = parse_datetime(clean_param)
                    if parsed is None:
                        parsed = datetime.fromisoformat(clean_param.replace("Z", "+00:00"))
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=timezone.utc)
                    since = parsed
            except (ValueError, TypeError):
                return Response(
                    {"detail": "Invalid 'since' timestamp format."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        limit_param = request.query_params.get("limit", 50)
        try:
            limit = min(int(limit_param), 100)
        except ValueError:
            limit = 50

        messages = list_elder_messages(elder_id=elder_id, since=since, limit=limit)
        serializer = MessageSerializer(messages, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request: Request, elder_id: uuid.UUID) -> Response:
        elder = get_object_or_404(Elder, id=elder_id)
        if not can(request.user, PermissionCode.SEND_MESSAGE, elder):
            return _messaging_error_response(
                AuthorizationDeniedError("User does not have permission to send messages.")
            )

        serializer = SendMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            message = send_message(
                elder_id=elder_id,
                direction=data["direction"],
                message_type=data["message_type"],
                body=data.get("body", ""),
                sender_user=request.user,
                sender_contact_id=data.get("sender_contact_id"),
                attachment_id=data.get("attachment_id"),
                idempotency_key=data.get("idempotency_key", ""),
            )
        except (InvalidMessageError, AttachmentNotFoundError) as exc:
            return _messaging_error_response(exc)

        return Response(
            MessageSerializer(message, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class MessageDeliveredView(APIView):
    """Mark a message as DELIVERED upon receipt by recipient."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, message_id: uuid.UUID) -> Response:
        try:
            message = mark_message_delivered(message_id=message_id, user_id=request.user.id)
        except (MessageNotFoundError, AuthorizationDeniedError) as exc:
            return _messaging_error_response(exc)

        return Response(
            MessageSerializer(message, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )


class MessageReadView(APIView):
    """Mark a message as READ when seen/listened to by recipient."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, message_id: uuid.UUID) -> Response:
        try:
            message = mark_message_read(message_id=message_id, user_id=request.user.id)
        except (MessageNotFoundError, AuthorizationDeniedError) as exc:
            return _messaging_error_response(exc)

        return Response(
            MessageSerializer(message, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )


class MediaUploadView(APIView):
    """Upload media file for voice note, image, or video attachment."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def dispatch(self, request, *args, **kwargs):
        """Temporarily elevate upload body limit for media uploads without compromising global security."""
        from django.conf import settings
        original_limit = getattr(settings, "DATA_UPLOAD_MAX_MEMORY_SIZE", 10 * 1024 * 1024)
        try:
            settings.DATA_UPLOAD_MAX_MEMORY_SIZE = 105 * 1024 * 1024  # 105 MB scoped to media upload only
            return super().dispatch(request, *args, **kwargs)
        finally:
            settings.DATA_UPLOAD_MAX_MEMORY_SIZE = original_limit

    def post(self, request: Request) -> Response:
        serializer = UploadMediaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        uploaded_file = data["file"]

        try:
            attachment = create_message_attachment(
                file_obj=uploaded_file.file,
                media_type=data["media_type"],
                claimed_mime_type=uploaded_file.content_type,
                original_filename=uploaded_file.name,
                duration_seconds=data.get("duration_seconds"),
                width=data.get("width"),
                height=data.get("height"),
            )
        except InvalidMediaError as exc:
            return _messaging_error_response(exc)

        return Response(
            MessageAttachmentSerializer(attachment).data,
            status=status.HTTP_201_CREATED,
        )


from rest_framework_simplejwt.authentication import JWTAuthentication


class QueryParamOrHeaderJWTAuthentication(JWTAuthentication):
    """Allows JWT authentication via Authorization header or ?token= query parameter for media streaming."""

    def authenticate(self, request: Request):
        header_auth = super().authenticate(request)
        if header_auth is not None:
            return header_auth

        raw_token = request.query_params.get("token")
        if raw_token:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token

        return None


class MediaDownloadView(APIView):
    """Secure streaming download of a media attachment."""

    authentication_classes = [QueryParamOrHeaderJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, attachment_id: uuid.UUID) -> StreamingHttpResponse:
        try:
            attachment = get_attachment(attachment_id=attachment_id)
            stream, file_size, mime_type = open_media_stream(attachment.file_path)
        except (AttachmentNotFoundError, MediaNotFoundError) as exc:
            raise Http404(str(exc))

        response = StreamingHttpResponse(stream, content_type=mime_type)
        response["Content-Length"] = str(file_size)
        response["Accept-Ranges"] = "bytes"
        # Never expose internal path or server headers
        response["Content-Disposition"] = f'inline; filename="{attachment.original_filename}"'
        return response
