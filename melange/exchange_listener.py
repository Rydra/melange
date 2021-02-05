import logging
from typing import Any

from funcy import lmap
from methoddispatch import singledispatch, SingleDispatch

from melange.infrastructure import Cache
from melange.utils import get_fully_qualified_name
from melange.infrastructure.cache import DedupCache

logger = logging.getLogger(__name__)


class ExchangeListener(SingleDispatch):
    """
    The domain event serializer is used to read the event data and then generate a proper
    object that can be used by the process dispatcher
    """

    def __init__(self, cache: DedupCache = None):
        self.cache = cache or Cache()

    def process_event(self, obj: Any, **kwargs):
        message_listener_key = (
            get_fully_qualified_name(self) + "." + kwargs["message_id"]
        )
        if message_listener_key in self.cache:
            logger.info("detected a duplicated message, ignoring")
            return

        self.process(obj, **kwargs)

        self.cache.store(message_listener_key, message_listener_key)

    def process(self, obj: Any, **kwargs):
        self._process(obj)

    @singledispatch
    def _process(self, event):
        """Event should be an instance of DomainEvent"""
        pass

    def listens_to(self):
        accepted_events = filter(lambda t: t is not object, self._process.registry)
        return lmap(lambda ev_type: ev_type.__name__, accepted_events)

    def accepts(self, manifest: str):
        """
        Default implementation. You can override this if you want, for example,
        to accept any manifest and not only the type of classes you listen
        (useful to override in the face of subclasses)
        """
        return not self.listens_to() or manifest in self.listens_to()


listener = ExchangeListener._process.register
