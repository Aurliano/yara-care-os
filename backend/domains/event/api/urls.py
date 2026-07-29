"""Read-only Event API routes."""

from django.urls import path

from domains.event.api.views import EventDetailView, EventRecordListView

urlpatterns = [
    path("events/", EventRecordListView.as_view(), name="event-record-list"),
    path("events/<uuid:event_id>/", EventDetailView.as_view(), name="event-detail"),
]
