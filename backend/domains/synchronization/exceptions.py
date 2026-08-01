"""Synchronization domain exceptions."""


class SynchronizationError(Exception):
    """Base synchronization error."""


class ReplicaNotFoundError(SynchronizationError):
    """Replica state was not found."""


class SessionNotFoundError(SynchronizationError):
    """Synchronization session was not found."""


class OperationNotFoundError(SynchronizationError):
    """Synchronization operation was not found."""


class ConflictNotFoundError(SynchronizationError):
    """Synchronization conflict was not found."""


class InvalidSessionStateError(SynchronizationError):
    """Session cannot transition to the requested state."""


class InvalidReplicaStateError(SynchronizationError):
    """Replica cannot perform the requested action."""


class ReplicaUnavailableError(SynchronizationError):
    """Replica is unavailable."""


class CheckpointMismatchError(SynchronizationError):
    """Checkpoint does not match expected value."""


class InvalidDeltaError(SynchronizationError):
    """Delta payload failed validation."""


class SnapshotCorruptedError(SynchronizationError):
    """Snapshot payload failed validation."""


class VersionMismatchError(SynchronizationError):
    """Aggregate version is incompatible."""


class SynchronizationConflictError(SynchronizationError):
    """A synchronization conflict blocks the operation."""


class ReplicaOutdatedError(SynchronizationError):
    """Replica state is outdated."""


class SynchronizationCancelledError(SynchronizationError):
    """Synchronization was cancelled."""


class SynchronizationTimeoutError(SynchronizationError):
    """Synchronization timed out."""


class IdempotencyConflictError(SynchronizationError):
    """Idempotency key reused with different payload."""
