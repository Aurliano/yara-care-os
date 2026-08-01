"""Synchronization API views."""

import uuid

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.api.errors import domain_error_response
from domains.synchronization.api.serializers import (
    CheckpointSerializer,
    ReplicaStateSerializer,
    ResolveConflictSerializer,
    StartSynchronizationSerializer,
    StatisticsSerializer,
    SubmitPayloadSerializer,
    SynchronizationConflictSerializer,
    SynchronizationOperationSerializer,
    SynchronizationSessionSerializer,
)
from domains.synchronization.exceptions import (
    ConflictNotFoundError,
    IdempotencyConflictError,
    InvalidDeltaError,
    InvalidReplicaStateError,
    InvalidSessionStateError,
    ReplicaNotFoundError,
    SessionNotFoundError,
    SnapshotCorruptedError,
    SynchronizationConflictError,
    SynchronizationError,
    VersionMismatchError,
)
from domains.synchronization.services.conflicts import get_conflicts, resolve_conflict
from domains.synchronization.services.operations import submit_aggregate_delta, submit_aggregate_snapshot
from domains.synchronization.services.replicas import (
    get_checkpoint,
    get_replica_state,
    get_synchronization_statistics,
    mark_replica_healthy,
    mark_replica_outdated,
    reset_replica,
)
from domains.synchronization.services.sessions import (
    cancel_synchronization,
    get_synchronization_history,
    get_synchronization_session,
    resume_synchronization,
    start_synchronization,
)


def _sync_error_response(exc: SynchronizationError) -> Response:
    return domain_error_response(
        exc,
        base_type=SynchronizationError,
        not_found=(SessionNotFoundError, ReplicaNotFoundError, ConflictNotFoundError),
        conflict=(
            InvalidSessionStateError,
            SynchronizationConflictError,
            VersionMismatchError,
            IdempotencyConflictError,
        ),
        bad_request=(InvalidDeltaError, SnapshotCorruptedError, InvalidReplicaStateError),
    )


class StartSynchronizationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = StartSynchronizationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            session = start_synchronization(
                replica_identifier=data["replica_identifier"],
                replica_type=data["replica_type"],
                direction=data["direction"],
                idempotency_key=data.get("idempotency_key") or None,
            )
        except SynchronizationError as exc:
            return _sync_error_response(exc)
        return Response(SynchronizationSessionSerializer(session).data, status=status.HTTP_201_CREATED)


class SessionPendingOperationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, session_id: uuid.UUID) -> Response:
        from domains.synchronization.services.operations import get_pending_operations

        try:
            get_synchronization_session(session_id)
        except SessionNotFoundError as exc:
            return _sync_error_response(exc)
        operations = get_pending_operations(session_id=session_id)
        return Response(SynchronizationOperationSerializer(operations, many=True).data)


class SessionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, session_id: uuid.UUID) -> Response:
        try:
            session = get_synchronization_session(session_id)
        except SessionNotFoundError as exc:
            return _sync_error_response(exc)
        return Response(SynchronizationSessionSerializer(session).data)


class SessionResumeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, session_id: uuid.UUID) -> Response:
        try:
            session = resume_synchronization(session_id=session_id)
        except SynchronizationError as exc:
            return _sync_error_response(exc)
        return Response(SynchronizationSessionSerializer(session).data)


class SessionCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, session_id: uuid.UUID) -> Response:
        try:
            session = cancel_synchronization(session_id=session_id)
        except SynchronizationError as exc:
            return _sync_error_response(exc)
        return Response(SynchronizationSessionSerializer(session).data)


class SessionSubmitDeltaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, session_id: uuid.UUID) -> Response:
        serializer = SubmitPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            operation = submit_aggregate_delta(
                session_id=session_id,
                aggregate_reference=data["aggregate_reference"],
                aggregate_version=data["aggregate_version"],
                payload=data["payload"],
                payload_type=data["payload_type"],
                payload_hash=data["payload_hash"],
                idempotency_key=data["idempotency_key"],
                expected_version=data.get("expected_version") or None,
            )
        except SynchronizationError as exc:
            return _sync_error_response(exc)
        return Response(SynchronizationOperationSerializer(operation).data, status=status.HTTP_201_CREATED)


class SessionSubmitSnapshotView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, session_id: uuid.UUID) -> Response:
        serializer = SubmitPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            operation = submit_aggregate_snapshot(
                session_id=session_id,
                aggregate_reference=data["aggregate_reference"],
                aggregate_version=data["aggregate_version"],
                payload=data["payload"],
                payload_type=data["payload_type"],
                payload_hash=data["payload_hash"],
                idempotency_key=data["idempotency_key"],
            )
        except SynchronizationError as exc:
            return _sync_error_response(exc)
        return Response(SynchronizationOperationSerializer(operation).data, status=status.HTTP_201_CREATED)


class ReplicaStateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, replica_identifier: uuid.UUID) -> Response:
        try:
            replica = get_replica_state(replica_identifier=replica_identifier)
        except ReplicaNotFoundError as exc:
            return _sync_error_response(exc)
        return Response(ReplicaStateSerializer(replica).data)


class ReplicaCheckpointView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, replica_identifier: uuid.UUID) -> Response:
        try:
            checkpoint = get_checkpoint(replica_identifier=replica_identifier)
        except ReplicaNotFoundError as exc:
            return _sync_error_response(exc)
        return Response(CheckpointSerializer(checkpoint).data)


class ReplicaStatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, replica_identifier: uuid.UUID) -> Response:
        try:
            stats = get_synchronization_statistics(replica_identifier=replica_identifier)
        except ReplicaNotFoundError as exc:
            return _sync_error_response(exc)
        return Response(StatisticsSerializer(stats).data)


class ReplicaHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, replica_identifier: uuid.UUID) -> Response:
        sessions = get_synchronization_history(replica_identifier=replica_identifier)
        return Response(SynchronizationSessionSerializer(sessions, many=True).data)


class ReplicaConflictsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, replica_identifier: uuid.UUID) -> Response:
        try:
            conflicts = get_conflicts(replica_identifier=replica_identifier)
        except ReplicaNotFoundError as exc:
            return _sync_error_response(exc)
        return Response(SynchronizationConflictSerializer(conflicts, many=True).data)


class ConflictResolveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, conflict_id: uuid.UUID) -> Response:
        serializer = ResolveConflictSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            conflict = resolve_conflict(
                conflict_id=conflict_id,
                resolution_payload=serializer.validated_data["resolution_payload"],
            )
        except SynchronizationError as exc:
            return _sync_error_response(exc)
        return Response(SynchronizationConflictSerializer(conflict).data)


class ReplicaResetView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, replica_identifier: uuid.UUID) -> Response:
        try:
            get_replica_state(replica_identifier=replica_identifier)
            replica = reset_replica(replica_identifier=replica_identifier)
        except ReplicaNotFoundError as exc:
            return _sync_error_response(exc)
        return Response(ReplicaStateSerializer(replica).data)


class ReplicaHealthView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, replica_identifier: uuid.UUID) -> Response:
        action = request.data.get("action", "healthy")
        try:
            if action == "outdated":
                replica = mark_replica_outdated(replica_identifier=replica_identifier)
            else:
                replica = mark_replica_healthy(replica_identifier=replica_identifier)
        except ReplicaNotFoundError as exc:
            return _sync_error_response(exc)
        return Response(ReplicaStateSerializer(replica).data)
