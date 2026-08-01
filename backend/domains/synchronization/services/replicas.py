"""Replica state commands and queries."""

from __future__ import annotations

import uuid

from django.db import transaction
from django.utils import timezone

from domains.synchronization.enums import ReplicaHealth, ReplicaStatus, ReplicaType
from domains.synchronization.exceptions import (
    CheckpointMismatchError,
    InvalidReplicaStateError,
    ReplicaNotFoundError,
    ReplicaUnavailableError,
)
from domains.synchronization.models import ReplicaState
from domains.synchronization.services.events import emit_checkpoint_advanced, emit_replica_updated


def get_replica_state(*, replica_identifier: uuid.UUID) -> ReplicaState:
    try:
        return ReplicaState.objects.get(replica_identifier=replica_identifier)
    except ReplicaState.DoesNotExist as exc:
        raise ReplicaNotFoundError("Replica state not found.") from exc


def get_replica_state_by_id(replica_state_id: uuid.UUID) -> ReplicaState:
    try:
        return ReplicaState.objects.get(pk=replica_state_id)
    except ReplicaState.DoesNotExist as exc:
        raise ReplicaNotFoundError("Replica state not found.") from exc


def get_or_create_replica_state(
    *,
    replica_identifier: uuid.UUID,
    replica_type: str,
) -> ReplicaState:
    if replica_type not in ReplicaType.values:
        raise InvalidReplicaStateError("Invalid replica type.")

    replica, created = ReplicaState.objects.get_or_create(
        replica_identifier=replica_identifier,
        defaults={
            "replica_type": replica_type,
            "health": ReplicaHealth.HEALTHY,
            "status": ReplicaStatus.IDLE,
        },
    )
    if created:
        emit_replica_updated(
            replica_state_id=replica.id,
            replica_identifier=replica.replica_identifier,
            discriminator="created",
        )
    return replica


def get_checkpoint(*, replica_identifier: uuid.UUID) -> dict:
    replica = get_replica_state(replica_identifier=replica_identifier)
    return {
        "replica_identifier": str(replica.replica_identifier),
        "checkpoint_sequence": replica.checkpoint_sequence,
        "checkpoint_token": str(replica.checkpoint_token) if replica.checkpoint_token else None,
    }


def get_synchronization_statistics(*, replica_identifier: uuid.UUID) -> dict:
    replica = get_replica_state(replica_identifier=replica_identifier)
    return {
        "replica_identifier": str(replica.replica_identifier),
        "statistics": replica.statistics,
        "last_successful_sync": replica.last_successful_sync.isoformat() if replica.last_successful_sync else None,
        "checkpoint_sequence": replica.checkpoint_sequence,
    }


def _ensure_replica_available(replica: ReplicaState) -> None:
    if replica.health == ReplicaHealth.UNAVAILABLE or replica.status == ReplicaStatus.UNAVAILABLE:
        raise ReplicaUnavailableError("Replica is unavailable.")


@transaction.atomic
def advance_checkpoint(
    *,
    replica_identifier: uuid.UUID,
    expected_checkpoint_sequence: int | None = None,
    checkpoint_token: uuid.UUID | None = None,
) -> ReplicaState:
    replica = ReplicaState.objects.select_for_update().get(replica_identifier=replica_identifier)

    if expected_checkpoint_sequence is not None and replica.checkpoint_sequence != expected_checkpoint_sequence:
        raise CheckpointMismatchError("Checkpoint sequence does not match.")

    new_sequence = replica.checkpoint_sequence + 1
    replica.checkpoint_sequence = new_sequence
    if checkpoint_token is not None:
        replica.checkpoint_token = checkpoint_token
    replica.last_successful_sync = timezone.now()
    replica.save(
        update_fields=[
            "checkpoint_sequence",
            "checkpoint_token",
            "last_successful_sync",
            "updated_at",
        ]
    )
    emit_checkpoint_advanced(
        replica_state_id=replica.id,
        checkpoint_sequence=new_sequence,
        checkpoint_token=replica.checkpoint_token,
    )
    return replica


@transaction.atomic
def reset_replica(*, replica_identifier: uuid.UUID) -> ReplicaState:
    replica = ReplicaState.objects.select_for_update().get(replica_identifier=replica_identifier)
    replica.status = ReplicaStatus.RESETTING
    replica.health = ReplicaHealth.OUTDATED
    replica.checkpoint_sequence = 0
    replica.checkpoint_token = None
    replica.statistics = {}
    replica.save(
        update_fields=[
            "status",
            "health",
            "checkpoint_sequence",
            "checkpoint_token",
            "statistics",
            "updated_at",
        ]
    )
    replica.aggregate_versions.all().delete()
    emit_replica_updated(
        replica_state_id=replica.id,
        replica_identifier=replica.replica_identifier,
        discriminator="reset",
    )
    return replica


@transaction.atomic
def mark_replica_healthy(*, replica_identifier: uuid.UUID) -> ReplicaState:
    replica = ReplicaState.objects.select_for_update().get(replica_identifier=replica_identifier)
    replica.health = ReplicaHealth.HEALTHY
    if replica.status in {ReplicaStatus.OUTDATED, ReplicaStatus.UNAVAILABLE}:
        replica.status = ReplicaStatus.IDLE
    replica.save(update_fields=["health", "status", "updated_at"])
    emit_replica_updated(
        replica_state_id=replica.id,
        replica_identifier=replica.replica_identifier,
        discriminator="healthy",
    )
    return replica


@transaction.atomic
def mark_replica_outdated(*, replica_identifier: uuid.UUID) -> ReplicaState:
    replica = ReplicaState.objects.select_for_update().get(replica_identifier=replica_identifier)
    replica.health = ReplicaHealth.OUTDATED
    replica.status = ReplicaStatus.OUTDATED
    replica.save(update_fields=["health", "status", "updated_at"])
    emit_replica_updated(
        replica_state_id=replica.id,
        replica_identifier=replica.replica_identifier,
        discriminator="outdated",
    )
    return replica


def set_replica_synchronizing(replica: ReplicaState) -> ReplicaState:
    _ensure_replica_available(replica)
    if replica.status == ReplicaStatus.SYNCHRONIZING:
        return replica
    replica.status = ReplicaStatus.SYNCHRONIZING
    replica.save(update_fields=["status", "updated_at"])
    return replica


def set_replica_idle(replica: ReplicaState) -> ReplicaState:
    if replica.status == ReplicaStatus.RESETTING:
        replica.status = ReplicaStatus.IDLE
        replica.health = ReplicaHealth.HEALTHY
    elif replica.status == ReplicaStatus.SYNCHRONIZING:
        replica.status = ReplicaStatus.IDLE
    replica.save(update_fields=["status", "health", "updated_at"])
    return replica
