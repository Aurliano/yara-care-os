from django.contrib import admin, messages
from domains.device.models import (
    Compartment,
    CompartmentAssignment,
    Device,
    DeviceAssignment,
    DeviceCapability,
    DeviceCapabilityOverride,
    DeviceCommand,
    DeviceModel,
    DeviceModelCapability,
    Pairing,
)
from domains.device.enums import DeviceOperationalStatus
from domains.device.services.assignments import assign_device, refurbish_device, return_device


class DeviceModelCapabilityInline(admin.TabularInline):
    model = DeviceModelCapability
    extra = 1


@admin.register(DeviceModel)
class DeviceModelAdmin(admin.ModelAdmin):
    list_display = ("model_code", "model_name", "manufacturer", "device_type", "status")
    list_filter = ("device_type", "status")
    search_fields = ("model_code", "model_name", "manufacturer")
    inlines = [DeviceModelCapabilityInline]


@admin.register(DeviceCapability)
class DeviceCapabilityAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


class DeviceAssignmentInline(admin.TabularInline):
    model = DeviceAssignment
    extra = 0
    fields = ("elder", "assignment_type", "status", "assigned_at", "unassigned_at")
    raw_id_fields = ("elder",)
    readonly_fields = ("created_at",)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("serial_number", "device_model", "operational_status", "last_seen_at", "created_at")
    list_filter = ("operational_status", "device_model__device_type", "device_model")
    search_fields = ("serial_number", "device_model__model_name")
    readonly_fields = ("created_at", "updated_at", "aggregate_version")
    inlines = [DeviceAssignmentInline]
    actions = ["action_mark_inventory", "action_return_device", "action_refurbish_device"]

    @admin.action(description="بازگشت دستگاه به انبار و لغو تخصیص (Return)")
    def action_return_device(self, request, queryset):
        count = 0
        for dev in queryset:
            try:
                return_device(device_id=dev.id)
                count += 1
            except Exception as e:
                self.message_user(request, f"خطا در دستگاه {dev.serial_number}: {e}", messages.ERROR)
        if count:
            self.message_user(request, f"{count} دستگاه با موفقیت مرجوع و وارد وضعیت بازگشتی شدند.", messages.SUCCESS)

    @admin.action(description="تعمیر/تایید سلامت دستگاه بازگشتی (Refurbish)")
    def action_refurbish_device(self, request, queryset):
        count = 0
        for dev in queryset:
            try:
                refurbish_device(device_id=dev.id)
                count += 1
            except Exception as e:
                self.message_user(request, f"خطا در دستگاه {dev.serial_number}: {e}", messages.ERROR)
        if count:
            self.message_user(request, f"{count} دستگاه آماده‌سازی و به انبار بازگشتند.", messages.SUCCESS)

    @admin.action(description="تغییر مستقیم وضعیت به آماده تخصیص در انبار (INVENTORY)")
    def action_mark_inventory(self, request, queryset):
        updated = queryset.update(operational_status=DeviceOperationalStatus.INVENTORY)
        self.message_user(request, f"وضعیت {updated} دستگاه به انبار تغییر یافت.", messages.SUCCESS)


@admin.register(DeviceAssignment)
class DeviceAssignmentAdmin(admin.ModelAdmin):
    list_display = ("device", "elder", "assignment_type", "status", "assigned_at", "unassigned_at")
    list_filter = ("status", "assignment_type")
    search_fields = ("device__serial_number", "elder__full_name")
    raw_id_fields = ("device", "elder")


@admin.register(Pairing)
class PairingAdmin(admin.ModelAdmin):
    list_display = ("hub_device", "peripheral_device", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("hub_device__serial_number", "peripheral_device__serial_number")
    raw_id_fields = ("hub_device", "peripheral_device")


@admin.register(Compartment)
class CompartmentAdmin(admin.ModelAdmin):
    list_display = ("device", "number", "label", "status")
    list_filter = ("status",)
    raw_id_fields = ("device",)


@admin.register(CompartmentAssignment)
class CompartmentAssignmentAdmin(admin.ModelAdmin):
    list_display = ("compartment", "care_activity_reference", "status", "assigned_at")
    list_filter = ("status",)
    raw_id_fields = ("compartment",)


@admin.register(DeviceCommand)
class DeviceCommandAdmin(admin.ModelAdmin):
    list_display = ("command_type", "target_device", "status", "created_at", "delivered_at")
    list_filter = ("command_type", "status")
    search_fields = ("target_device__serial_number",)
    raw_id_fields = ("target_device",)
    readonly_fields = ("created_at", "delivered_at", "executing_at", "completed_at")


@admin.register(DeviceCapabilityOverride)
class DeviceCapabilityOverrideAdmin(admin.ModelAdmin):
    list_display = ("device", "capability", "state", "effective_at")
    list_filter = ("state",)
    raw_id_fields = ("device",)
