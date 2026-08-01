from django.urls import path

from domains.synchronization.api.views import (
    ConflictResolveView,
    ReplicaCheckpointView,
    ReplicaConflictsView,
    ReplicaHealthView,
    ReplicaHistoryView,
    ReplicaResetView,
    ReplicaStateView,
    ReplicaStatisticsView,
    SessionCancelView,
    SessionDetailView,
    SessionPendingOperationsView,
    SessionResumeView,
    SessionSubmitDeltaView,
    SessionSubmitSnapshotView,
    StartSynchronizationView,
)

urlpatterns = [
    path("synchronization/sessions/start/", StartSynchronizationView.as_view(), name="sync-session-start"),
    path("synchronization/sessions/<uuid:session_id>/", SessionDetailView.as_view(), name="sync-session-detail"),
    path(
        "synchronization/sessions/<uuid:session_id>/pending-operations/",
        SessionPendingOperationsView.as_view(),
        name="sync-session-pending-operations",
    ),
    path("synchronization/sessions/<uuid:session_id>/resume/", SessionResumeView.as_view(), name="sync-session-resume"),
    path("synchronization/sessions/<uuid:session_id>/cancel/", SessionCancelView.as_view(), name="sync-session-cancel"),
    path(
        "synchronization/sessions/<uuid:session_id>/delta/",
        SessionSubmitDeltaView.as_view(),
        name="sync-session-submit-delta",
    ),
    path(
        "synchronization/sessions/<uuid:session_id>/snapshot/",
        SessionSubmitSnapshotView.as_view(),
        name="sync-session-submit-snapshot",
    ),
    path(
        "synchronization/replicas/<uuid:replica_identifier>/",
        ReplicaStateView.as_view(),
        name="sync-replica-state",
    ),
    path(
        "synchronization/replicas/<uuid:replica_identifier>/checkpoint/",
        ReplicaCheckpointView.as_view(),
        name="sync-replica-checkpoint",
    ),
    path(
        "synchronization/replicas/<uuid:replica_identifier>/statistics/",
        ReplicaStatisticsView.as_view(),
        name="sync-replica-statistics",
    ),
    path(
        "synchronization/replicas/<uuid:replica_identifier>/history/",
        ReplicaHistoryView.as_view(),
        name="sync-replica-history",
    ),
    path(
        "synchronization/replicas/<uuid:replica_identifier>/conflicts/",
        ReplicaConflictsView.as_view(),
        name="sync-replica-conflicts",
    ),
    path(
        "synchronization/replicas/<uuid:replica_identifier>/reset/",
        ReplicaResetView.as_view(),
        name="sync-replica-reset",
    ),
    path(
        "synchronization/replicas/<uuid:replica_identifier>/health/",
        ReplicaHealthView.as_view(),
        name="sync-replica-health",
    ),
    path(
        "synchronization/conflicts/<uuid:conflict_id>/resolve/",
        ConflictResolveView.as_view(),
        name="sync-conflict-resolve",
    ),
]
