from datetime import timedelta
from django.contrib import admin, messages
from django.utils import timezone
from domains.licensing.models import (
    Entitlement,
    License,
    LicensePlanHistory,
    Plan,
    PlanEntitlement,
    Subscription,
)
from domains.licensing.enums import LicenseStatus, SubscriptionStatus
from domains.licensing.services.subscriptions import activate_subscription


class PlanEntitlementInline(admin.TabularInline):
    model = PlanEntitlement
    extra = 1


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("code", "name")
    inlines = [PlanEntitlementInline]


@admin.register(Entitlement)
class EntitlementAdmin(admin.ModelAdmin):
    list_display = ("key", "kind", "description")
    list_filter = ("kind",)
    search_fields = ("key", "description")


class SubscriptionInline(admin.TabularInline):
    model = Subscription
    extra = 0
    fields = ("plan", "status", "started_at", "expires_at", "auto_renew", "is_trial")
    readonly_fields = ("created_at",)


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ("elder", "plan", "status", "valid_from", "valid_until", "created_at")
    list_filter = ("status", "plan")
    search_fields = ("elder__full_name", "plan__code", "plan__name")
    raw_id_fields = ("elder",)
    readonly_fields = ("created_at",)
    inlines = [SubscriptionInline]
    actions = ["action_activate_free_trial", "action_extend_one_month", "action_activate_without_payment"]

    @admin.action(description="فعال‌سازی ۳۰ روزه بدون نیاز به پرداخت آنلاین")
    def action_activate_without_payment(self, request, queryset):
        count = 0
        now = timezone.now()
        for license_obj in queryset:
            sub = license_obj.subscriptions.filter(status=SubscriptionStatus.PENDING_PAYMENT).first()
            if sub:
                activate_subscription(subscription_id=sub.id)
            else:
                license_obj.status = LicenseStatus.ACTIVE
                if not license_obj.valid_from:
                    license_obj.valid_from = now
                license_obj.valid_until = now + timedelta(days=30)
                license_obj.save(update_fields=["status", "valid_from", "valid_until"])
                Subscription.objects.create(
                    license=license_obj,
                    plan=license_obj.plan,
                    status=SubscriptionStatus.ACTIVE,
                    started_at=now,
                    expires_at=now + timedelta(days=30),
                    auto_renew=False,
                    is_trial=False,
                )
            count += 1
        self.message_user(request, f"{count} لایسنس به صورت دستی فعال و ۳۰ روز تمدید شد.", messages.SUCCESS)

    @admin.action(description="فعال‌سازی اشتراک آزمایشی ۱۴ روزه")
    def action_activate_free_trial(self, request, queryset):
        count = 0
        now = timezone.now()
        for license_obj in queryset:
            license_obj.status = LicenseStatus.ACTIVE
            if not license_obj.valid_from:
                license_obj.valid_from = now
            license_obj.valid_until = now + timedelta(days=14)
            license_obj.save(update_fields=["status", "valid_from", "valid_until"])
            Subscription.objects.create(
                license=license_obj,
                plan=license_obj.plan,
                status=SubscriptionStatus.ACTIVE,
                started_at=now,
                expires_at=now + timedelta(days=14),
                auto_renew=False,
                is_trial=True,
            )
            count += 1
        self.message_user(request, f"{count} لایسنس با پلن آزمایشی ۱۴ روزه فعال گردید.", messages.SUCCESS)

    @admin.action(description="تمدید اعتبار ۳۰ روزه به لایسنس‌های فعال")
    def action_extend_one_month(self, request, queryset):
        count = 0
        now = timezone.now()
        for license_obj in queryset:
            base_date = license_obj.valid_until if (license_obj.valid_until and license_obj.valid_until > now) else now
            license_obj.valid_until = base_date + timedelta(days=30)
            license_obj.status = LicenseStatus.ACTIVE
            license_obj.save(update_fields=["status", "valid_until"])
            count += 1
        self.message_user(request, f"اعتبار {count} لایسنس برای ۳۰ روز دیگر افزایش یافت.", messages.SUCCESS)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("license", "plan", "status", "started_at", "expires_at", "is_trial", "auto_renew")
    list_filter = ("status", "is_trial", "plan")
    search_fields = ("license__elder__full_name", "plan__code")
    raw_id_fields = ("license",)
    actions = ["action_activate_manual"]

    @admin.action(description="تایید دستی پرداخت و فعال‌سازی فوری اشتراک")
    def action_activate_manual(self, request, queryset):
        count = 0
        for sub in queryset:
            if sub.status in {SubscriptionStatus.PENDING_PAYMENT, SubscriptionStatus.PAST_DUE}:
                activate_subscription(subscription_id=sub.id)
                count += 1
        self.message_user(request, f"{count} اشتراک با موفقیت فعال شد.", messages.SUCCESS)


@admin.register(LicensePlanHistory)
class LicensePlanHistoryAdmin(admin.ModelAdmin):
    list_display = ("license", "previous_plan", "new_plan", "changed_at")
    search_fields = ("license__elder__full_name",)
    readonly_fields = ("license", "previous_plan", "new_plan", "changed_at")
