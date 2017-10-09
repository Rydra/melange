from melange.eventbus.async_eventbus import AsynchronousEventBus
from melange.eventbus.sync_eventbus import DomainEventBus


class EventBusFactory:
    @staticmethod
    def create(synchronous=False, *args, **kwargs):
        return AsynchronousEventBus(*args, **kwargs) if not synchronous else DomainEventBus(*args, **kwargs)
