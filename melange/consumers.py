import logging
from typing import Any, Callable, List, Optional

from funcy import lmap
from methoddispatch import SingleDispatch, singledispatch

logger = logging.getLogger(__name__)


class Consumer:
    def __init__(self, on_message: Optional[Callable[[Any], None]] = None) -> None:
        self._on_message = on_message

    def process(self, message: Any, **kwargs: Any) -> None:
        if self._on_message:
            self._on_message(message)

    def accepts(self, manifest: Optional[str]) -> bool:
        return True


class SingleDispatchConsumer(Consumer, SingleDispatch):
    """
    This class can consume events from a queue and pass them to a processor
    """

    def process(self, message: Any, **kwargs: Any) -> None:
        self._process(message)

    @singledispatch
    def _process(self, message: Any) -> None:
        """Event should be an instance of DomainEvent"""
        pass

    def listens_to(self) -> List[str]:
        accepted_events = filter(lambda t: t is not object, self._process.registry)
        return lmap(lambda ev_type: ev_type.__name__, accepted_events)

    def accepts(self, manifest: Optional[str]) -> bool:
        """
        Default implementation. You can override this if you want, for example,
        to accept any manifest and not only the type of classes you listen
        (useful to override in the face of subclasses)
        """
        return not self.listens_to() or manifest in self.listens_to()


consumer = SingleDispatchConsumer._process.register
