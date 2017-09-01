from melange.eventbus.async_eventbus import AsynchronousEventBus
from melange.eventbus.sync_eventbus import SynchronousEventBus


class EventBusFactory:
    @staticmethod
    def create(synchronous=False, *args, **kwargs):
        return AsynchronousEventBus(*args, **kwargs) if not synchronous else SynchronousEventBus(*args, **kwargs)
