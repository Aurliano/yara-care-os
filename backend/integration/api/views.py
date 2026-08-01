"""Hub-facing integration API."""

from __future__ import annotations

import uuid

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from domains.event.services.queries import get_pending_outbox_count
from domains.synchronization.services.operations import submit_aggregate_delta, submit_aggregate_snapshot
from integration.context import IntegrationContext
from integration.observability.metrics import snapshot
from integration.runtime.adapters.communication import (
    accept_hub_session,
    end_hub_session,
    record_hub_call_attempt,
    report_hub_attempt_result,
)
from integration.runtime.adapters.confirmations import submit_hub_confirmation
from integration.runtime.adapters.device import (
    complete_hub_command,
    deliver_hub_command,
    fail_hub_command,
    update_hub_device_state,
)
from integration.runtime.adapters.synchronization import start_download_session, start_upload_session
from integration.runtime.scheduler import run_integration_cycle


def _ctx_from_request(request: Request) -> IntegrationContext:
    correlation_id = request.headers.get("X-Correlation-ID", "")
    replica_header = request.headers.get("X-Replica-ID")
    device_header = request.headers.get("X-Device-ID")
    actor_id = request.user.id if request.user and request.user.is_authenticated else None
    ctx = IntegrationContext.new(correlation_id=correlation_id or None)
    if replica_header:
        ctx = ctx.with_replica(uuid.UUID(replica_header))
    if device_header:
        ctx = ctx.with_device(uuid.UUID(device_header))
    if actor_id:
        ctx = ctx.with_actor(actor_id)
    return ctx


class RuntimeHealthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(
            {
                "status": "ok",
                "pending_outbox": get_pending_outbox_count(),
                "metrics": snapshot(),
            }
        )


class RuntimeProcessView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        ctx = _ctx_from_request(request)
        result = run_integration_cycle(ctx)
        return Response(result)


class HubConfirmationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        ctx = _ctx_from_request(request)
        data = request.data
        result = submit_hub_confirmation(
            ctx,
            execution_id=uuid.UUID(data["workflow_execution_id"]),
            interaction_reference=data["interaction_reference"],
            evidence_type=data.get("evidence_type", "HUB_CONFIRMATION"),
        )
        return Response(result, status=status.HTTP_200_OK)


class HubDeviceStateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        ctx = _ctx_from_request(request)
        data = request.data
        result = update_hub_device_state(
            ctx,
            device_id=uuid.UUID(data["device_id"]),
            current_state=data["current_state"],
            is_online=data.get("is_online"),
        )
        return Response(result)


class HubCommandDeliverView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, command_id: uuid.UUID) -> Response:
        ctx = _ctx_from_request(request)
        return Response(deliver_hub_command(ctx, command_id=command_id))


class HubCommandCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, command_id: uuid.UUID) -> Response:
        ctx = _ctx_from_request(request)
        return Response(complete_hub_command(ctx, command_id=command_id, result=request.data.get("result")))


class HubCommandFailView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, command_id: uuid.UUID) -> Response:
        ctx = _ctx_from_request(request)
        return Response(fail_hub_command(ctx, command_id=command_id, reason=request.data.get("reason", "")))


class HubSyncStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        ctx = _ctx_from_request(request)
        direction = request.data.get("direction", "UPLOAD")
        idempotency_key = request.data.get("idempotency_key", str(uuid.uuid4()))
        if direction == "DOWNLOAD":
            session = start_download_session(ctx, idempotency_key=idempotency_key)
        else:
            session = start_upload_session(ctx, idempotency_key=idempotency_key)
        return Response(
            {
                "session_id": str(session.id),
                "status": session.status,
                "synchronization_token": str(session.synchronization_token),
            },
            status=status.HTTP_201_CREATED,
        )


class HubSyncDeltaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, session_id: uuid.UUID) -> Response:
        data = request.data
        operation = submit_aggregate_delta(
            session_id=session_id,
            aggregate_reference=uuid.UUID(data["aggregate_reference"]),
            aggregate_version=data["aggregate_version"],
            payload=data["payload"],
            payload_type=data["payload_type"],
            payload_hash=data["payload_hash"],
            idempotency_key=data["idempotency_key"],
        )
        return Response({"operation_id": str(operation.id), "status": operation.status}, status=status.HTTP_201_CREATED)


class HubSyncSnapshotView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, session_id: uuid.UUID) -> Response:
        data = request.data
        operation = submit_aggregate_snapshot(
            session_id=session_id,
            aggregate_reference=uuid.UUID(data["aggregate_reference"]),
            aggregate_version=data["aggregate_version"],
            payload=data["payload"],
            payload_type=data["payload_type"],
            payload_hash=data["payload_hash"],
            idempotency_key=data["idempotency_key"],
        )
        return Response({"operation_id": str(operation.id), "status": operation.status}, status=status.HTTP_201_CREATED)


class HubSessionAcceptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, session_id: uuid.UUID) -> Response:
        ctx = _ctx_from_request(request)
        return Response(accept_hub_session(ctx, session_id=session_id))


class HubSessionEndView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, session_id: uuid.UUID) -> Response:
        ctx = _ctx_from_request(request)
        return Response(end_hub_session(ctx, session_id=session_id))
