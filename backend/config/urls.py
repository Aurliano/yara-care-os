"""Root URL configuration."""

from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "سامانه مدیریت و پشتیبانی سایدا"
admin.site.site_title = "پنل ادمین سایدا"
admin.site.index_title = "مدیریت تجهیزات، اشتراک‌ها و پرونده‌های مراقبت"

urlpatterns = [
    path("sayda-admin/", admin.site.urls),
    path("", include("application.landing.urls")),
    path("api/v1/", include("common.urls")),
    path("api/v1/", include("domains.identity_access.api.urls")),
    path("api/v1/", include("domains.licensing.api.urls")),
    path("api/v1/", include("domains.event.api.urls")),
    path("api/v1/", include("domains.scheduling.api.urls")),
    path("api/v1/", include("domains.workflow.api.urls")),
    path("api/v1/", include("domains.care.api.urls")),
    path("api/v1/", include("domains.device.api.urls")),
    path("api/v1/", include("domains.communication.api.urls")),
    path("api/v1/", include("domains.notification.api.urls")),
    path("api/v1/", include("domains.synchronization.api.urls")),
    path("api/v1/", include("infrastructure.communication.api.urls")),
    path("api/v1/", include("integration.api.urls")),
    path("api/v1/", include("application.payments.api.urls")),
]
