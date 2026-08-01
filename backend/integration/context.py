"""Integration context propagated across orchestration."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, replace


@dataclass(frozen=True, slots=True)
class IntegrationContext:
    correlation_id: str = ""
    execution_id: uuid.UUID | None = None
    replica_id: uuid.UUID | None = None
    actor_id: uuid.UUID | None = None
    device_id: uuid.UUID | None = None

    @classmethod
    def new(cls, *, correlation_id: str | None = None) -> IntegrationContext:
        return cls(correlation_id=correlation_id or str(uuid.uuid4()))

    def with_execution(self, execution_id: uuid.UUID) -> IntegrationContext:
        return replace(self, execution_id=execution_id)

    def with_replica(self, replica_id: uuid.UUID) -> IntegrationContext:
        return replace(self, replica_id=replica_id)

    def with_actor(self, actor_id: uuid.UUID) -> IntegrationContext:
        return replace(self, actor_id=actor_id)

    def with_device(self, device_id: uuid.UUID) -> IntegrationContext:
        return replace(self, device_id=device_id)
