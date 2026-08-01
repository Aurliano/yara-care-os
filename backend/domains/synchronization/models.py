"""Synchronization domain models."""

from __future__ import annotations

import uuid

from django.db import models

from domains.synchronization.enums import (
    ConflictStatus,
    ConflictType,
    OperationStatus,
    OperationType,
    ReplicaHealth,
    ReplicaStatus,
    ReplicaType,
    SessionStatus,
    SyncDirection,
)


class ReplicaState(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    replica_identifier = models.UUIDField(unique=True)
    replica_type = models.CharField(max_length=16, choices=ReplicaType.choices)
    health = models.CharField(
        max_length=16,
        choices=ReplicaHealth.choices,
        default=ReplicaHealth.HEALTHY,
    )
    status = models.CharField(
        max_length=16,
        choices=ReplicaStatus.choices,
        default=ReplicaStatus.IDLE,
    )
    checkpoint_sequence = models.PositiveBigIntegerField(default=0)
    checkpoint_token = models.UUIDField(null=True, blank=True)
    last_successful_sync = models.DateTimeField(null=True, blank=True)
    statistics = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "synchronization_replica_state"
        indexes = [
            models.Index(fields=["replica_identifier"], name="sync_replica_identifier_idx"),
            models.Index(fields=["status"], name="sync_replica_status_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.replica_identifier}:{self.status}"


class SynchronizationSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    replica_state = models.ForeignKey(
        ReplicaState,
        on_delete=models.PROTECT,
        related_name="sessions",
    )
    direction = models.CharField(max_length=16, choices=SyncDirection.choices)
    status = models.CharField(
        max_length=32,
        choices=SessionStatus.choices,
        default=SessionStatus.SYNCHRONIZATION_REQUESTED,
    )
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    statistics = models.JSONField(default=dict)
    synchronization_token = models.UUIDField(default=uuid.uuid4, editable=False)
    idempotency_key = models.CharField(max_length=128, unique=True, null=True, blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "synchronization_session"
        indexes = [
            models.Index(fields=["replica_state", "started_at"], name="sync_session_replica_idx"),
            models.Index(fields=["status"], name="sync_session_status_idx"),
            models.Index(fields=["synchronization_token"], name="sync_session_token_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.id}:{self.status}"


class SynchronizationOperation(models.Model):
    """Immutable audit record of one replication attempt; not a transport queue."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    synchronization_session = models.ForeignKey(
        SynchronizationSession,
        on_delete=models.CASCADE,
        related_name="operations",
    )
    operation_type = models.CharField(max_length=16, choices=OperationType.choices)
    aggregate_reference = models.UUIDField()
    aggregate_version = models.CharField(max_length=64)
    payload = models.JSONField()
    payload_type = models.CharField(max_length=64)
    payload_hash = models.CharField(max_length=64)
    status = models.CharField(
        max_length=16,
        choices=OperationStatus.choices,
        default=OperationStatus.PENDING,
    )
    idempotency_key = models.CharField(max_length=128, unique=True)
    failure_reason = models.CharField(max_length=255, blank=True, default="")
    started_at = models.DateTimeField()
    applied_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "synchronization_operation"
        indexes = [
            models.Index(fields=["synchronization_session", "started_at"], name="sync_op_session_idx"),
            models.Index(fields=["aggregate_reference"], name="sync_op_aggregate_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.operation_type}:{self.status}"


class SynchronizationConflict(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    replica_state = models.ForeignKey(
        ReplicaState,
        on_delete=models.CASCADE,
        related_name="conflicts",
    )
    synchronization_session = models.ForeignKey(
        SynchronizationSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conflicts",
    )
    aggregate_reference = models.UUIDField()
    conflict_type = models.CharField(max_length=32, choices=ConflictType.choices)
    status = models.CharField(
        max_length=16,
        choices=ConflictStatus.choices,
        default=ConflictStatus.OPEN,
    )
    local_version = models.CharField(max_length=64, blank=True, default="")
    remote_version = models.CharField(max_length=64, blank=True, default="")
    resolution_payload = models.JSONField(null=True, blank=True)
    detected_at = models.DateTimeField()
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "synchronization_conflict"
        indexes = [
            models.Index(fields=["replica_state", "status"], name="sync_conflict_replica_idx"),
            models.Index(fields=["aggregate_reference"], name="sync_conflict_aggregate_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.conflict_type}:{self.status}"


class ReplicaVersion(models.Model):
    """Entity owned by ReplicaState tracking last-known aggregate version per replica."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    replica_state = models.ForeignKey(
        ReplicaState,
        on_delete=models.CASCADE,
        related_name="aggregate_versions",
    )
    aggregate_reference = models.UUIDField()
    aggregate_version = models.CharField(max_length=64)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "synchronization_replica_version"
        constraints = [
            models.UniqueConstraint(
                fields=["replica_state", "aggregate_reference"],
                name="sync_replica_version_unique_aggregate",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.aggregate_reference}:{self.aggregate_version}"
