from datetime import datetime

import pytz


class DomainEvent:
    def __init__(self, occurred_on=None, metadata=None, correlation_id=None):
        self.occurred_on = occurred_on or datetime.now(pytz.utc)
        self.metadata = metadata or {}
        self.correlation_id = correlation_id

    def set_metadata(self, metadata):
        self.metadata = metadata

    def get_occurred_on(self):
        return self.occurred_on

    def emit(self, **kwargs):
        from melange.domain_event_bus import DomainEventBus

        DomainEventBus().publish(self, **kwargs)
        return self
