from django.db import models


class SyncDirection(models.TextChoices):
    UPLOAD = "UPLOAD", "Upload"
    DOWNLOAD = "DOWNLOAD", "Download"


class ReplicaType(models.TextChoices):
    BACKEND = "BACKEND", "Backend"
    HUB = "HUB", "Hub"


class ReplicaHealth(models.TextChoices):
    HEALTHY = "HEALTHY", "Healthy"
    OUTDATED = "OUTDATED", "Outdated"
    UNAVAILABLE = "UNAVAILABLE", "Unavailable"


class ReplicaStatus(models.TextChoices):
    IDLE = "IDLE", "Idle"
    SYNCHRONIZING = "SYNCHRONIZING", "Synchronizing"
    RESETTING = "RESETTING", "Resetting"
    OUTDATED = "OUTDATED", "Outdated"
    UNAVAILABLE = "UNAVAILABLE", "Unavailable"


class SessionStatus(models.TextChoices):
    SYNCHRONIZATION_REQUESTED = "SYNCHRONIZATION_REQUESTED", "Synchronization Requested"
    SESSION_STARTED = "SESSION_STARTED", "Session Started"
    PAYLOAD_RECEIVED = "PAYLOAD_RECEIVED", "Payload Received"
    VALIDATION = "VALIDATION", "Validation"
    CHANGES_APPLIED = "CHANGES_APPLIED", "Changes Applied"
    CHECKPOINT_ADVANCED = "CHECKPOINT_ADVANCED", "Checkpoint Advanced"
    SESSION_COMPLETED = "SESSION_COMPLETED", "Session Completed"
    TRANSFER_FAILED = "TRANSFER_FAILED", "Transfer Failed"
    RETRY_SCHEDULED = "RETRY_SCHEDULED", "Retry Scheduled"
    SYNCHRONIZATION_RESUMED = "SYNCHRONIZATION_RESUMED", "Synchronization Resumed"
    CANCELLED = "CANCELLED", "Cancelled"


TERMINAL_SESSION_STATUSES = frozenset(
    {
        SessionStatus.SESSION_COMPLETED,
        SessionStatus.CANCELLED,
    }
)

RESUMABLE_SESSION_STATUSES = frozenset(
    {
        SessionStatus.TRANSFER_FAILED,
        SessionStatus.RETRY_SCHEDULED,
    }
)


class OperationType(models.TextChoices):
    DELTA = "DELTA", "Delta"
    SNAPSHOT = "SNAPSHOT", "Snapshot"


class OperationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    VALIDATED = "VALIDATED", "Validated"
    APPLIED = "APPLIED", "Applied"
    FAILED = "FAILED", "Failed"


class ConflictType(models.TextChoices):
    CONCURRENT_CHANGE = "CONCURRENT_CHANGE", "Concurrent Change"
    CHECKPOINT_MISMATCH = "CHECKPOINT_MISMATCH", "Checkpoint Mismatch"
    VERSION_MISMATCH = "VERSION_MISMATCH", "Version Mismatch"


class ConflictStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    RESOLVED = "RESOLVED", "Resolved"
