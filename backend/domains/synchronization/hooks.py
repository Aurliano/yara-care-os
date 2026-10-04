"""Synchronization domain hooks and extension points."""

import uuid
from typing import Any, Callable

_replica_access_checker: Callable[[Any, uuid.UUID], bool] | None = None


def register_replica_access_checker(checker: Callable[[Any, uuid.UUID], bool]) -> None:
    """Register an authorizer callback to check user access to a replica/device."""
    global _replica_access_checker
    _replica_access_checker = checker


def can_access_replica(user: Any, replica_identifier: uuid.UUID) -> bool:
    """Check if the given user is authorized to access the replica."""
    if _replica_access_checker is not None:
        return _replica_access_checker(user, replica_identifier)
    return True
