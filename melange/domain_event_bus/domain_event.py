from datetime import datetime

import pytz


class DomainEvent:
    def __init__(self, occurred_on=None):
        self.occurred_on = occurred_on or datetime.now(pytz.utc)

    def get_occurred_on(self):
        return self.occurred_on

    def emit(self, **kwargs):
        from melange.domain_event_bus import DomainEventBus
        DomainEventBus().publish(self, **kwargs)
        return self
