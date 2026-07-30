"""Scheduling API routes."""

from django.urls import path

from domains.scheduling.api.views import (
    OccurrenceCancelView,
    OccurrenceDetailView,
    OccurrenceSkipView,
    ScheduleCancelView,
    ScheduleDetailView,
    ScheduleExceptionCreateView,
    ScheduleListCreateView,
    ScheduleOccurrenceQueryView,
    SchedulePauseView,
    ScheduleResumeView,
)

urlpatterns = [
    path("schedules/", ScheduleListCreateView.as_view(), name="scheduling-schedule-list-create"),
    path("schedules/<uuid:schedule_id>/", ScheduleDetailView.as_view(), name="scheduling-schedule-detail"),
    path("schedules/<uuid:schedule_id>/pause/", SchedulePauseView.as_view(), name="scheduling-schedule-pause"),
    path("schedules/<uuid:schedule_id>/resume/", ScheduleResumeView.as_view(), name="scheduling-schedule-resume"),
    path("schedules/<uuid:schedule_id>/cancel/", ScheduleCancelView.as_view(), name="scheduling-schedule-cancel"),
    path(
        "schedules/<uuid:schedule_id>/exceptions/",
        ScheduleExceptionCreateView.as_view(),
        name="scheduling-schedule-exception-create",
    ),
    path(
        "schedules/<uuid:schedule_id>/occurrences/",
        ScheduleOccurrenceQueryView.as_view(),
        name="scheduling-schedule-occurrences",
    ),
    path("occurrences/<uuid:occurrence_id>/", OccurrenceDetailView.as_view(), name="scheduling-occurrence-detail"),
    path("occurrences/<uuid:occurrence_id>/skip/", OccurrenceSkipView.as_view(), name="scheduling-occurrence-skip"),
    path(
        "occurrences/<uuid:occurrence_id>/cancel/",
        OccurrenceCancelView.as_view(),
        name="scheduling-occurrence-cancel",
    ),
]
