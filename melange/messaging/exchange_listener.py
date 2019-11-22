import logging

from melange.infrastructure import Cache
from .event_message import EventMessage
from .utils import get_fully_qualified_name


logger = logging.getLogger(__name__)


class ExchangeListener:
    def __init__(self, cache: Cache = None):
        self.cache = cache or Cache.instance()

    def process_event(self, event, **kwargs):
        message_listener_key = get_fully_qualified_name(self) + '.' + kwargs['message_id']
        if message_listener_key in self.cache:
            logger.info('detected a duplicated message, ignoring')
            return

        self.process(event, **kwargs)

        self.cache.store(message_listener_key, message_listener_key)

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
        # None = listens to every event
        return None

    def accepts(self, event_type_name):
        return not self.listens_to() or event_type_name in self.listens_to()
