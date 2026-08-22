from django.urls import path

from domains.notification.api.views import ElderAlertDetailView, ElderAlertListView

urlpatterns = [
    path("elders/<uuid:elder_id>/alerts/", ElderAlertListView.as_view(), name="notification-elder-alerts"),
    path(
        "elders/<uuid:elder_id>/alerts/<uuid:alert_id>/",
        ElderAlertDetailView.as_view(),
        name="notification-elder-alert-detail",
    ),
]
