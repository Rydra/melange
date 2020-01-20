import logging

from funcy import lmap
from methoddispatch import singledispatch, SingleDispatch

from melange.cqrs.interfaces import DomainEventSerializer, DedupCache
from melange.infrastructure import Cache
from .utils import get_fully_qualified_name

logger = logging.getLogger(__name__)


class ExchangeListener(SingleDispatch):
    def __init__(self, domain_event_serializer: DomainEventSerializer, cache: DedupCache = None):
        self.cache = cache or Cache()
        self.domain_event_serializer = domain_event_serializer

    def process_event(self, event, **kwargs):
        message_listener_key = get_fully_qualified_name(self) + '.' + kwargs['message_id']
        if message_listener_key in self.cache:
            logger.info('detected a duplicated message, ignoring')
            return

        self.process(event, **kwargs)

        self.cache.store(message_listener_key, message_listener_key)

    def process(self, event, **kwargs):
        deserialized_event = self.domain_event_serializer.deserialize(event['data'], event['name'])
        self._process(deserialized_event)

    @singledispatch
    def _process(self, event):
        """Event should be an instance of DomainEvent"""
        pass

    def listens_to(self):
        accepted_events = filter(lambda t: t is not object, self._process.registry)
        return lmap(lambda ev: ev.__name__, accepted_events)

    def accepts(self, event_type_name):
        return not self.listens_to() or event_type_name in self.listens_to()


listener = ExchangeListener._process.register
