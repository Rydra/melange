from typing import List, Optional

from melange.domain_event_bus import DomainEvent


class EventStream:
    def __init__(self, events: List[DomainEvent], version: Optional[int]):
        self.events = events
        self.version = version

    @staticmethod
    def new(events=None):
        return EventStream(events or [], None)
