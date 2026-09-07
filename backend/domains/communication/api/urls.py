from django.urls import path

from domains.communication.api.messaging_views import (
    ElderMessagesView,
    MediaDownloadView,
    MediaUploadView,
    MessageDeliveredView,
    MessageReadView,
)
from domains.communication.api.views import (
    CallAttemptResultView,
    ContactArchiveView,
    ContactDetailView,
    ContactPriorityView,
    ElderContactListCreateView,
    ElderPriorityContactsView,
    ElderSessionListCreateView,
    SessionAcceptView,
    SessionCallAttemptsView,
    SessionCancelView,
    SessionDeclineView,
    SessionDetailView,
    SessionEndView,
    SessionParticipantsView,
)

urlpatterns = [
    # Messaging & Media
    path("elders/<uuid:elder_id>/messages/", ElderMessagesView.as_view(), name="communication-elder-messages"),
    path("messages/<uuid:message_id>/delivered/", MessageDeliveredView.as_view(), name="communication-message-delivered"),
    path("messages/<uuid:message_id>/read/", MessageReadView.as_view(), name="communication-message-read"),
    path("media/upload/", MediaUploadView.as_view(), name="communication-media-upload"),
    path("media/<uuid:attachment_id>/download/", MediaDownloadView.as_view(), name="communication-media-download"),
    path(
        "elders/<uuid:elder_id>/contacts/",
        ElderContactListCreateView.as_view(),
        name="communication-elder-contacts",
    ),
    path(
        "elders/<uuid:elder_id>/contacts/priority/",
        ElderPriorityContactsView.as_view(),
        name="communication-elder-priority-contacts",
    ),
    path("contacts/<uuid:contact_id>/", ContactDetailView.as_view(), name="communication-contact-detail"),
    path("contacts/<uuid:contact_id>/archive/", ContactArchiveView.as_view(), name="communication-contact-archive"),
    path("contacts/<uuid:contact_id>/priority/", ContactPriorityView.as_view(), name="communication-contact-priority"),
    path(
        "elders/<uuid:elder_id>/sessions/",
        ElderSessionListCreateView.as_view(),
        name="communication-elder-sessions",
    ),
    path("sessions/<uuid:session_id>/", SessionDetailView.as_view(), name="communication-session-detail"),
    path(
        "sessions/<uuid:session_id>/participants/",
        SessionParticipantsView.as_view(),
        name="communication-session-participants",
    ),
    path(
        "sessions/<uuid:session_id>/attempts/",
        SessionCallAttemptsView.as_view(),
        name="communication-session-attempts",
    ),
    path("sessions/<uuid:session_id>/accept/", SessionAcceptView.as_view(), name="communication-session-accept"),
    path("sessions/<uuid:session_id>/decline/", SessionDeclineView.as_view(), name="communication-session-decline"),
    path("sessions/<uuid:session_id>/cancel/", SessionCancelView.as_view(), name="communication-session-cancel"),
    path("sessions/<uuid:session_id>/end/", SessionEndView.as_view(), name="communication-session-end"),
    path("call-attempts/<uuid:attempt_id>/result/", CallAttemptResultView.as_view(), name="communication-attempt-result"),
]
