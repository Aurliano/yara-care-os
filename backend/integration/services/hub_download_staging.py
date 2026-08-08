"""Stage pending download operations for hub synchronization sessions."""

from __future__ import annotations

import json
import uuid
from datetime import timedelta
from typing import Any

from django.db import transaction
from django.utils import timezone

from domains.care.models import CareActivity
from domains.care.services.sync_export import build_care_activity_sync_delta
from domains.communication.models import CommunicationSession
from domains.communication.services.contacts import get_elder_contacts
from domains.communication.services.sync_export import build_communication_session_sync_delta
from domains.device.enums import AssignmentStatus, CommandStatus
from domains.device.models import Device, DeviceCommand
from domains.device.services.assignments import get_assignments
from domains.device.services.sync_export import build_device_sync_delta
from domains.scheduling.models import Occurrence, ScheduleDefinition
from domains.synchronization.enums import OperationStatus, OperationType, SessionStatus, SyncDirection
from domains.synchronization.exceptions import InvalidSessionStateError
from domains.synchronization.identity import compare_aggregate_versions, compute_payload_hash
from domains.synchronization.models import ReplicaVersion, SynchronizationOperation, SynchronizationSession
from domains.synchronization.services.replicas import advance_checkpoint, get_replica_state
from domains.workflow.models import WorkflowDefinition, WorkflowExecution
from domains.workflow.services.sync_export import build_workflow_execution_sync_delta
from integration.context import IntegrationContext
from integration.exceptions import ReplicaContextRequiredError

INCREMENTAL_HORIZON_DAYS = 7


def _epoch_millis(value) -> int:
    if value is None:
        return 0
    return int(value.timestamp() * 1000)


def _resolve_elder_id(ctx: IntegrationContext) -> uuid.UUID | None:
    if ctx.device_id is None:
        return None
    assignments = get_assignments(device_id=ctx.device_id)
    active = next((item for item in assignments if item.status == AssignmentStatus.ASSIGNED), None)
    return active.elder_id if active else None


def _elder_schedule_ids(*, elder_id: uuid.UUID) -> list[uuid.UUID]:
    return list(
        CareActivity.objects.filter(elder_id=elder_id).values_list("schedule_definition_id", flat=True)
    )


def _occurrence_ids_in_horizon(*, schedule_ids: list[uuid.UUID]) -> list[uuid.UUID]:
    if not schedule_ids:
        return []
    horizon = timezone.now() + timedelta(days=INCREMENTAL_HORIZON_DAYS)
    return list(
        Occurrence.objects.filter(
            schedule_definition_id__in=schedule_ids,
            scheduled_for__lte=horizon,
        ).values_list("id", flat=True)
    )


def _incoming_is_newer(*, replica, aggregate_reference: uuid.UUID, incoming_version: str) -> bool:
    current = ReplicaVersion.objects.filter(
        replica_state=replica,
        aggregate_reference=aggregate_reference,
    ).first()
    if current is None:
        return True
    return compare_aggregate_versions(
        incoming=incoming_version,
        current=current.aggregate_version,
    ) > 0


def _record_replica_version(*, replica, aggregate_reference: uuid.UUID, aggregate_version: str) -> None:
    ReplicaVersion.objects.update_or_create(
        replica_state=replica,
        aggregate_reference=aggregate_reference,
        defaults={"aggregate_version": aggregate_version},
    )


def _seed_replica_versions_for_scope(*, replica, elder_id: uuid.UUID, device_id: uuid.UUID | None) -> None:
    for activity in CareActivity.objects.filter(elder_id=elder_id):
        _record_replica_version(
            replica=replica,
            aggregate_reference=activity.id,
            aggregate_version=str(activity.aggregate_version),
        )

    schedule_ids = _elder_schedule_ids(elder_id=elder_id)
    occurrence_ids = _occurrence_ids_in_horizon(schedule_ids=schedule_ids)
    if occurrence_ids:
        for execution in WorkflowExecution.objects.filter(occurrence_id__in=occurrence_ids):
            _record_replica_version(
                replica=replica,
                aggregate_reference=execution.id,
                aggregate_version=str(execution.aggregate_version),
            )

    if device_id is not None:
        device = Device.objects.filter(pk=device_id).first()
        if device is not None:
            _record_replica_version(
                replica=replica,
                aggregate_reference=device.id,
                aggregate_version=str(device.aggregate_version),
            )

    for session in CommunicationSession.objects.filter(elder_id=elder_id):
        _record_replica_version(
            replica=replica,
            aggregate_reference=session.id,
            aggregate_version=str(session.aggregate_version),
        )


def _stage_delta_from_builder(
    *,
    session: SynchronizationSession,
    builder,
    id_suffix: str,
) -> SynchronizationOperation:
    delta = builder()
    return _stage_pending_operation(
        session=session,
        operation_type=OperationType.DELTA,
        aggregate_reference=delta["aggregate_reference"],
        aggregate_version=delta["aggregate_version"],
        payload=delta["payload"],
        payload_type=delta["payload_type"],
        idempotency_key=f"hub-download:{session.id}:{id_suffix}",
    )


def _stage_incremental_deltas(
    *,
    session: SynchronizationSession,
    replica,
    elder_id: uuid.UUID,
    device_id: uuid.UUID | None,
) -> int:
    staged = 0

    for activity in CareActivity.objects.filter(elder_id=elder_id):
        incoming_version = str(activity.aggregate_version)
        if not _incoming_is_newer(
            replica=replica,
            aggregate_reference=activity.id,
            incoming_version=incoming_version,
        ):
            continue
        _stage_delta_from_builder(
            session=session,
            builder=lambda activity_id=activity.id: build_care_activity_sync_delta(care_activity_id=activity_id),
            id_suffix=f"care:{activity.id}",
        )
        staged += 1

    schedule_ids = _elder_schedule_ids(elder_id=elder_id)
    occurrence_ids = _occurrence_ids_in_horizon(schedule_ids=schedule_ids)
    if occurrence_ids:
        for execution in WorkflowExecution.objects.filter(occurrence_id__in=occurrence_ids):
            incoming_version = str(execution.aggregate_version)
            if not _incoming_is_newer(
                replica=replica,
                aggregate_reference=execution.id,
                incoming_version=incoming_version,
            ):
                continue
            _stage_delta_from_builder(
                session=session,
                builder=lambda execution_id=execution.id: build_workflow_execution_sync_delta(
                    execution_id=execution_id,
                ),
                id_suffix=f"workflow:{execution.id}",
            )
            staged += 1

    if device_id is not None:
        device = Device.objects.filter(pk=device_id).first()
        if device is not None and _incoming_is_newer(
            replica=replica,
            aggregate_reference=device.id,
            incoming_version=str(device.aggregate_version),
        ):
            _stage_delta_from_builder(
                session=session,
                builder=lambda device_id=device.id: build_device_sync_delta(device_id=device_id),
                id_suffix=f"device:{device.id}",
            )
            staged += 1

    for comm_session in CommunicationSession.objects.filter(elder_id=elder_id):
        incoming_version = str(comm_session.aggregate_version)
        if not _incoming_is_newer(
            replica=replica,
            aggregate_reference=comm_session.id,
            incoming_version=incoming_version,
        ):
            continue
        _stage_delta_from_builder(
            session=session,
            builder=lambda session_id=comm_session.id: build_communication_session_sync_delta(
                session_id=session_id,
            ),
            id_suffix=f"communication:{comm_session.id}",
        )
        staged += 1

    return staged


def _build_elder_snapshot_payload(*, elder_id: uuid.UUID, device_id: uuid.UUID | None) -> dict[str, Any]:
    activities = list(
        CareActivity.objects.filter(elder_id=elder_id)
        .select_related("schedule_definition", "workflow_definition", "prescription")
        .order_by("created_at")
    )
    schedule_ids = [activity.schedule_definition_id for activity in activities]
    workflow_definition_ids = [activity.workflow_definition_id for activity in activities]

    prescriptions = []
    for activity in activities:
        prescription = getattr(activity, "prescription", None)
        if prescription is None:
            continue
        prescriptions.append(
            {
                "care_activity_id": str(activity.id),
                "medication_reference": prescription.medication_reference,
                "dosage_information": prescription.dosage_information,
                "elder_friendly_description": prescription.elder_friendly_description,
                "personalized_description": prescription.personalized_description,
                "media_reference": str(prescription.media_reference) if prescription.media_reference else None,
            }
        )

    schedule_definitions = []
    occurrences = []
    if schedule_ids:
        for schedule in ScheduleDefinition.objects.filter(id__in=schedule_ids):
            schedule_definitions.append(
                {
                    "id": str(schedule.id),
                    "owner_reference": schedule.owner_reference,
                    "recurrence_definition_json": json.dumps(schedule.recurrence_definition),
                    "timezone": schedule.timezone,
                    "start_at_epoch_millis": _epoch_millis(schedule.start_at),
                    "end_at_epoch_millis": _epoch_millis(schedule.end_at),
                    "status": schedule.status,
                    "updated_at_epoch_millis": _epoch_millis(schedule.updated_at),
                }
            )
        horizon = timezone.now() + timedelta(days=INCREMENTAL_HORIZON_DAYS)
        for occurrence in Occurrence.objects.filter(schedule_definition_id__in=schedule_ids, scheduled_for__lte=horizon):
            occurrences.append(
                {
                    "id": str(occurrence.id),
                    "schedule_definition_id": str(occurrence.schedule_definition_id),
                    "scheduled_for_epoch_millis": _epoch_millis(occurrence.scheduled_for),
                    "status": occurrence.status,
                    "updated_at_epoch_millis": _epoch_millis(occurrence.created_at),
                }
            )

    workflow_definitions = []
    for definition in WorkflowDefinition.objects.filter(id__in=workflow_definition_ids):
        workflow_definitions.append(
            {
                "id": str(definition.id),
                "code": definition.code,
                "name": definition.name,
                "status": definition.status,
                "definition_json": json.dumps(definition.definition),
                "updated_at_epoch_millis": _epoch_millis(definition.updated_at),
            }
        )

    occurrence_ids = [uuid.UUID(item["id"]) for item in occurrences]
    workflow_executions = []
    if occurrence_ids:
        for execution in WorkflowExecution.objects.filter(occurrence_id__in=occurrence_ids):
            workflow_executions.append(
                {
                    "workflow_execution_id": str(execution.id),
                    "occurrence_id": str(execution.occurrence_id),
                    "workflow_definition_id": str(execution.workflow_definition_id),
                    "status": execution.status,
                    "current_step": execution.current_step,
                    "postpone_count": execution.postpone_count,
                    "retry_count": execution.retry_count,
                    "escalation_index": execution.escalation_index,
                    "current_action_json": json.dumps(execution.current_action),
                    "active_until_epoch_millis": _epoch_millis(execution.active_until),
                    "started_at_epoch_millis": _epoch_millis(execution.started_at),
                    "completed_at_epoch_millis": _epoch_millis(execution.completed_at),
                    "updated_at_epoch_millis": _epoch_millis(execution.updated_at),
                }
            )

    devices = []
    device_commands = []
    if device_id is not None:
        devices.append(
            {
                "device_id": str(device_id),
                "serial_number": Device.objects.filter(pk=device_id).values_list("serial_number", flat=True).first() or "",
                "operational_status": Device.objects.filter(pk=device_id).values_list("operational_status", flat=True).first() or "",
                "current_state": Device.objects.filter(pk=device_id).values_list("current_state", flat=True).first() or {},
                "updated_at_epoch_millis": int(timezone.now().timestamp() * 1000),
            }
        )
        for command in DeviceCommand.objects.filter(target_device_id=device_id, status=CommandStatus.QUEUED):
            device_commands.append(
                {
                    "id": str(command.id),
                    "target_device_id": str(command.target_device_id),
                    "command_type": command.command_type,
                    "parameters_json": json.dumps(command.parameters),
                    "status": command.status,
                    "expires_at_epoch_millis": _epoch_millis(command.expires_at),
                    "result_json": json.dumps(command.result),
                    "failure_reason": command.failure_reason,
                    "idempotency_key": command.idempotency_key,
                    "execution_reference": str(command.execution_reference) if command.execution_reference else None,
                    "updated_at_epoch_millis": _epoch_millis(command.created_at),
                }
            )

    contacts = []
    for contact in get_elder_contacts(elder_id=elder_id):
        contacts.append(
            {
                "id": str(contact.id),
                "elder_id": str(contact.elder_id),
                "display_name": contact.display_name,
                "phone": contact.phone,
                "communication_identities_json": json.dumps(contact.communication_identities),
                "preferred_channel": contact.preferred_channel,
                "photo_reference": contact.photo_reference,
                "is_priority": contact.is_priority,
                "status": contact.status,
                "updated_at_epoch_millis": _epoch_millis(contact.updated_at),
            }
        )

    care_activities = []
    for activity in activities:
        care_activities.append(
            {
                "care_activity_id": str(activity.id),
                "elder_id": str(activity.elder_id),
                "activity_type": activity.activity_type,
                "status": activity.status,
                "display_title": activity.display_title,
                "display_subtitle": activity.display_subtitle,
                "display_icon": activity.display_icon,
                "schedule_definition_id": str(activity.schedule_definition_id),
                "workflow_definition_id": str(activity.workflow_definition_id),
                "confirmation_requirement_json": json.dumps(activity.confirmation_requirement),
                "compartment_assignment_reference": activity.compartment_assignment_reference,
                "updated_at_epoch_millis": _epoch_millis(activity.updated_at),
            }
        )

    return {
        "care_activities": care_activities,
        "prescriptions": prescriptions,
        "workflow_definitions": workflow_definitions,
        "workflow_executions": workflow_executions,
        "schedule_definitions": schedule_definitions,
        "occurrences": occurrences,
        "devices": devices,
        "device_commands": device_commands,
        "communication_sessions": [],
        "contacts": contacts,
    }


def _stage_pending_operation(
    *,
    session: SynchronizationSession,
    operation_type: str,
    aggregate_reference: uuid.UUID,
    aggregate_version: str,
    payload: dict[str, Any],
    payload_type: str,
    idempotency_key: str,
) -> SynchronizationOperation:
    return SynchronizationOperation.objects.create(
        synchronization_session=session,
        operation_type=operation_type,
        aggregate_reference=aggregate_reference,
        aggregate_version=aggregate_version,
        payload=payload,
        payload_type=payload_type,
        payload_hash=compute_payload_hash(payload=payload),
        idempotency_key=idempotency_key,
        status=OperationStatus.PENDING,
        started_at=timezone.now(),
    )


def stage_hub_download_operations(*, ctx: IntegrationContext, session: SynchronizationSession) -> int:
    """Populate pending operations for a hub DOWNLOAD session using existing sync contracts."""
    if ctx.replica_id is None:
        raise ReplicaContextRequiredError("replica_id is required")

    if session.direction != SyncDirection.DOWNLOAD:
        return 0

    elder_id = _resolve_elder_id(ctx)
    if elder_id is None:
        return 0

    replica = get_replica_state(replica_identifier=ctx.replica_id)
    checkpoint = replica.checkpoint_sequence

    if checkpoint == 0:
        payload = _build_elder_snapshot_payload(elder_id=elder_id, device_id=ctx.device_id)
        aggregate_reference = uuid.uuid5(uuid.NAMESPACE_URL, f"hub-snapshot:{elder_id}")
        _stage_pending_operation(
            session=session,
            operation_type=OperationType.SNAPSHOT,
            aggregate_reference=aggregate_reference,
            aggregate_version="1",
            payload=payload,
            payload_type="hub.replica.snapshot",
            idempotency_key=f"hub-snapshot:{session.id}",
        )
        return 1

    return _stage_incremental_deltas(
        session=session,
        replica=replica,
        elder_id=elder_id,
        device_id=ctx.device_id,
    )


@transaction.atomic
def complete_hub_download_session(*, ctx: IntegrationContext, session_id: uuid.UUID) -> dict[str, Any]:
    """Mark download operations consumed and advance replica checkpoint after hub apply."""
    if ctx.replica_id is None:
        raise ReplicaContextRequiredError("replica_id is required")

    from domains.synchronization.services.sessions import _complete_session, _transition_session

    session = SynchronizationSession.objects.select_for_update().get(pk=session_id)
    if session.direction != SyncDirection.DOWNLOAD:
        raise InvalidSessionStateError("Session is not a download session.")

    replica = session.replica_state
    pending = list(
        SynchronizationOperation.objects.filter(
            synchronization_session=session,
            status=OperationStatus.PENDING,
        )
    )
    if not pending:
        _complete_session(session)
        return {"status": session.status, "operations_applied": 0}

    had_snapshot = any(
        operation.operation_type == OperationType.SNAPSHOT or operation.payload_type.endswith(".snapshot")
        for operation in pending
    )

    for operation in pending:
        operation.status = OperationStatus.APPLIED
        operation.applied_at = timezone.now()
        operation.save(update_fields=["status", "applied_at"])
        if operation.operation_type == OperationType.DELTA:
            _record_replica_version(
                replica=replica,
                aggregate_reference=operation.aggregate_reference,
                aggregate_version=operation.aggregate_version,
            )

    elder_id = _resolve_elder_id(ctx)
    if had_snapshot and elder_id is not None:
        _seed_replica_versions_for_scope(
            replica=replica,
            elder_id=elder_id,
            device_id=ctx.device_id,
        )

    _transition_session(session, SessionStatus.CHANGES_APPLIED)
    advance_checkpoint(
        replica_identifier=ctx.replica_id,
        checkpoint_token=session.synchronization_token,
    )
    _transition_session(session, SessionStatus.CHECKPOINT_ADVANCED)
    _complete_session(session)
    return {"status": session.status, "operations_applied": len(pending)}
