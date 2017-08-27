from geeteventbus.async_eventbus import AsynchronousEventBus
from geeteventbus.sync_eventbus import SynchronousEventBus


class EventBusFactory:
    @staticmethod
    def create(synchronous=False, *args, **kwargs):
        return AsynchronousEventBus(*args, **kwargs) if not synchronous else SynchronousEventBus(*args, **kwargs)