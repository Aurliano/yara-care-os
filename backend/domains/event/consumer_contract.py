"""Consumer idempotency contract (not a processing framework).

Future Event consumers — whether in-process handlers or Synchronization
transports — must honor:

1. ``event_id`` is the sole idempotency key for event processing.
2. At-least-once delivery is expected; duplicate envelopes with the same
   ``event_id`` must not repeat business side effects.
3. ``correlation_id`` and ``causation_id`` are tracing metadata only and
   must not be used as deduplication keys.
4. Consumers own their reaction semantics; Event records facts only.
"""

from __future__ import annotations

import uuid
from typing import Protocol

from domains.event.models import EventRecord


class IdempotentEventConsumer(Protocol):
    """Minimal contract for idempotent event processing."""

    def already_processed(self, event_id: uuid.UUID) -> bool:
        """Return whether this consumer has applied side effects for event_id."""

    def mark_processed(self, event_id: uuid.UUID) -> None:
        """Persist consumer-side processing completion for event_id."""

    def handle_event(self, event: EventRecord) -> None:
        """Apply business reaction once per event_id."""
