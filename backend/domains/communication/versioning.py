"""Communication aggregate version ownership for synchronization."""

from __future__ import annotations

from domains.communication.models import CommunicationSession


def bump_communication_session_version(session: CommunicationSession, update_fields: list[str]) -> list[str]:
    """Increment monotonic aggregate version owned by Communication."""
    session.aggregate_version += 1
    if "aggregate_version" not in update_fields:
        update_fields.append("aggregate_version")
    return update_fields
