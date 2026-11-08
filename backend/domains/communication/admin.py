from django.contrib import admin
from domains.communication.models import (
    CallAttempt,
    CommunicationSession,
    Contact,
    Message,
    MessageAttachment,
    MessageRecipient,
    SessionParticipant,
)
from domains.identity_access.models import Membership


@admin.action(description="ایجاد مخاطب تبلت برای مراقبان این سالمند (Sync Caregivers to Hub)")
def sync_caregivers_to_hub_contacts(modeladmin, request, queryset):
    created_count = 0
    for contact in queryset:
        elder = contact.elder
        memberships = Membership.objects.filter(elder=elder, status="ACTIVE").select_related("user")
        for m in memberships:
            phone = m.user.phone or ""
            display_name = m.relationship or m.user.full_name or phone or "مراقب"
            _, created = Contact.objects.get_or_create(
                elder=elder,
                phone=phone,
                defaults={
                    "display_name": display_name,
                    "is_priority": m.is_primary,
                    "preferred_channel": "VOICE",
                    "status": "ACTIVE",
                },
            )
            if created:
                created_count += 1
    modeladmin.message_user(
        request,
        f"{created_count} مخاطب جدید از میان مراقبان برای تبلت هاب ایجاد شد.",
    )


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "elder",
        "phone",
        "preferred_channel",
        "is_priority",
        "status",
        "created_at",
    )
    list_filter = ("status", "is_priority", "preferred_channel")
    search_fields = ("display_name", "phone", "elder__full_name")
    raw_id_fields = ("elder",)
    ordering = ("-is_priority", "display_name")
    actions = [sync_caregivers_to_hub_contacts]


class SessionParticipantInline(admin.TabularInline):
    model = SessionParticipant
    extra = 0
    raw_id_fields = ("contact",)


class CallAttemptInline(admin.TabularInline):
    model = CallAttempt
    extra = 0


@admin.register(CommunicationSession)
class CommunicationSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "elder",
        "channel",
        "status",
        "outcome",
        "initiated_at",
        "connected_at",
        "ended_at",
    )
    list_filter = ("channel", "status", "outcome")
    search_fields = ("elder__full_name",)
    raw_id_fields = ("elder",)
    ordering = ("-initiated_at",)
    inlines = [SessionParticipantInline, CallAttemptInline]


class MessageRecipientInline(admin.TabularInline):
    model = MessageRecipient
    extra = 0


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "elder",
        "sender_contact",
        "direction",
        "message_type",
        "status",
        "created_at",
    )
    list_filter = ("direction", "message_type", "status")
    search_fields = ("elder__full_name", "body")
    raw_id_fields = ("elder", "sender_contact", "attachment")
    ordering = ("-created_at",)
    inlines = [MessageRecipientInline]


@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "original_filename", "mime_type", "file_size", "created_at")
    search_fields = ("original_filename", "file_path")

