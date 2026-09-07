"""Serializers for communication messaging API."""

from __future__ import annotations

from rest_framework import serializers

from domains.communication.enums import MessageDirection, MessageStatus, MessageType
from domains.communication.models import Message, MessageAttachment


class MessageAttachmentSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()
    media_type = serializers.SerializerMethodField()

    class Meta:
        model = MessageAttachment
        fields = [
            "id",
            "media_type",
            "file_size",
            "mime_type",
            "duration_seconds",
            "width",
            "height",
            "original_filename",
            "created_at",
            "download_url",
        ]
        read_only_fields = fields

    def get_download_url(self, obj: MessageAttachment) -> str:
        return f"/api/v1/media/{obj.id}/download/"

    def get_media_type(self, obj: MessageAttachment) -> str:
        mime = (obj.mime_type or "").lower()
        if mime.startswith("audio/"):
            return "VOICE"
        if mime.startswith("image/"):
            return "IMAGE"
        if mime.startswith("video/"):
            return "VIDEO"
        return "UNKNOWN"


class MessageSenderSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    is_hub = serializers.BooleanField(read_only=True)


class MessageSerializer(serializers.ModelSerializer):
    attachment = MessageAttachmentSerializer(read_only=True)
    sender = serializers.SerializerMethodField()
    sender_display_name = serializers.SerializerMethodField()
    sender_user_id = serializers.SerializerMethodField()
    delivered = serializers.SerializerMethodField()
    read = serializers.SerializerMethodField()
    delivered_at = serializers.SerializerMethodField()
    read_at = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id",
            "elder_id",
            "direction",
            "message_type",
            "body",
            "status",
            "idempotency_key",
            "created_at",
            "sent_at",
            "delivered",
            "delivered_at",
            "read",
            "read_at",
            "sender",
            "sender_display_name",
            "sender_user_id",
            "attachment",
        ]
        read_only_fields = fields

    def _get_recipient(self, obj: Message):
        user = self.context.get("user")
        if not user:
            request = self.context.get("request")
            if request and getattr(request, "user", None) and request.user.is_authenticated:
                user = request.user
        if not user or not getattr(user, "id", None):
            return None
        user_id = user.id
        for recipient in obj.recipients.all():
            if recipient.user_id == user_id:
                return recipient
        return None

    def get_delivered_at(self, obj: Message) -> str | None:
        recipient = self._get_recipient(obj)
        if recipient and recipient.delivered_at:
            return recipient.delivered_at.isoformat()
        return None

    def get_read_at(self, obj: Message) -> str | None:
        recipient = self._get_recipient(obj)
        if recipient and recipient.read_at:
            return recipient.read_at.isoformat()
        return None

    def get_delivered(self, obj: Message) -> bool:
        recipient = self._get_recipient(obj)
        return bool(recipient and recipient.delivered_at is not None)

    def get_read(self, obj: Message) -> bool:
        recipient = self._get_recipient(obj)
        return bool(recipient and recipient.read_at is not None)

    def get_status(self, obj: Message) -> str:
        recipient = self._get_recipient(obj)
        if recipient:
            if recipient.read_at is not None:
                return MessageStatus.READ
            if recipient.delivered_at is not None:
                return MessageStatus.DELIVERED
        return obj.status

    def get_sender(self, obj: Message) -> dict:
        if obj.direction == MessageDirection.HUB_TO_FAMILY:
            contact_name = obj.sender_contact.display_name if obj.sender_contact else "Elder (Hub)"
            return {
                "id": str(obj.sender_contact_id) if obj.sender_contact_id else None,
                "display_name": contact_name,
                "is_hub": True,
            }
        display_name = "خانواده"
        if obj.sender_user_id:
            try:
                from domains.identity_access.models import User
                user = User.objects.filter(id=obj.sender_user_id).first()
                if user and user.full_name:
                    display_name = user.full_name
            except Exception:
                pass
        return {
            "id": str(obj.sender_user_id) if obj.sender_user_id else None,
            "display_name": display_name,
            "is_hub": False,
        }

    def get_sender_display_name(self, obj: Message) -> str:
        sender_dict = self.get_sender(obj)
        return sender_dict.get("display_name", "")

    def get_sender_user_id(self, obj: Message) -> str | None:
        return str(obj.sender_user_id) if obj.sender_user_id else None


class SendMessageSerializer(serializers.Serializer):
    direction = serializers.ChoiceField(choices=MessageDirection.choices)
    message_type = serializers.ChoiceField(choices=MessageType.choices)
    body = serializers.CharField(required=False, allow_blank=True, default="")
    attachment_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    sender_contact_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    idempotency_key = serializers.CharField(required=False, allow_blank=True, default="", max_length=64)


class UploadMediaSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
    media_type = serializers.ChoiceField(choices=MessageType.choices)
    duration_seconds = serializers.FloatField(required=False, allow_null=True, default=None)
    width = serializers.IntegerField(required=False, allow_null=True, default=None)
    height = serializers.IntegerField(required=False, allow_null=True, default=None)
