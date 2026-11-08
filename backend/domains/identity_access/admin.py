from django.contrib import admin
from domains.identity_access.models import (
    Elder,
    EmergencyRecipient,
    Invitation,
    Membership,
    Permission,
    Role,
    RolePermission,
    User,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("phone", "full_name", "email", "status", "is_staff", "is_superuser", "created_at")
    list_filter = ("status", "is_staff", "is_superuser")
    search_fields = ("phone", "full_name", "email")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    fields = ("user", "role", "relationship", "is_primary", "status", "joined_at")
    raw_id_fields = ("user",)


@admin.register(Elder)
class ElderAdmin(admin.ModelAdmin):
    list_display = ("full_name", "birth_date", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("full_name",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [MembershipInline]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "elder", "role", "relationship", "is_primary", "status", "joined_at")
    list_filter = ("status", "is_primary", "role")
    search_fields = ("user__phone", "user__full_name", "elder__full_name")
    raw_id_fields = ("user", "elder")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ("role", "permission")
    list_filter = ("role",)


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("elder", "invited_by", "role", "invite_code", "status", "expires_at", "created_at")
    list_filter = ("status",)
    search_fields = ("invite_code", "elder__full_name", "invited_by__phone")
    raw_id_fields = ("elder", "invited_by")


@admin.register(EmergencyRecipient)
class EmergencyRecipientAdmin(admin.ModelAdmin):
    list_display = ("elder", "membership", "priority", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("elder__full_name", "membership__user__full_name", "membership__user__phone")
    raw_id_fields = ("elder", "membership")
