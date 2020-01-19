from methoddispatch import singledispatch

from melange.domain_event_bus import DomainEventHandler


class Debugger(DomainEventHandler):
    @singledispatch
    def process(self, event):
        print(f"Event received: {type(event).__name__} at {event.occurred_on.isoformat()}")
