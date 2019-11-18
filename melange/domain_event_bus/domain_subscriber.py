""" Subscriber super-class """
from .domain_event_bus import DomainEvent


class DomainEventHandler:
    def process(self, event, **kwargs):
        """
        Called by the domain_event_bus.

        :param event: The event object
        :type event: EventMessage or subclass of event

        This method implements the logic for processing the event. This method should not block for
        long time as that will affect the performance of the domain_event_bus.
        """
        pass

    def listens_to(self):
        return []

    def listen(self):
        from melange.domain_event_bus import DomainEventBus
        DomainEventBus.instance().subscribe(self)
        return self

    def accepts(self, event):
        return isinstance(event, DomainEvent) \
               and (self.listens_to() == [] or any(isinstance(event, e) for e in self.listens_to()))
