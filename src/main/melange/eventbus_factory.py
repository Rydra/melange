from melange.async_eventbus import AsynchronousEventBus
from melange.sync_eventbus import SynchronousEventBus


class EventBusFactory:
    @staticmethod
    def create(synchronous=False, *args, **kwargs):
        return AsynchronousEventBus(*args, **kwargs) if not synchronous else SynchronousEventBus(*args, **kwargs)