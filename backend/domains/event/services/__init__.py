"""Public Event domain service interface.

Contract mapping (Frozen Event Domain Contract V1.1):

- RecordEvent -> record_event
- PublishEvent -> publish_event
- GetEvent -> get_event
- GetEventsByCorrelation -> get_events_by_correlation
- GetEventsByProducer -> get_events_by_producer
- GetEventsSince -> get_events_since

GetEventsForEntity is deferred until a generic entity-reference contract exists.
"""

from domains.event.services.queries import (
    get_event,
    get_events_by_correlation,
    get_events_by_producer,
    get_events_since,
)
from domains.event.services.recording import EventInput, publish_event, record_event

__all__ = [
    "EventInput",
    "get_event",
    "get_events_by_correlation",
    "get_events_by_producer",
    "get_events_since",
    "publish_event",
    "record_event",
]
