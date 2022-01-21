import logging
from typing import Any, Callable, Optional

from methoddispatch import SingleDispatch, singledispatch

logger = logging.getLogger(__name__)


class Consumer:
    """
    A consumer is responsible to process a message and do
    whatever is needed by the application.

    You could use is as is and supply a `on_message` callable to process your messages.
    Though commonly you would inherit this class, create your own consumer and
    override the `process` and `accepts` methods.
    """

    def __init__(self, on_message: Optional[Callable[[Any], None]] = None) -> None:
        self._on_message = on_message

    def process(self, message: Any, **kwargs: Any) -> None:
        """
        Processes a message
        Args:
            message: the message data to process, already deserialied
            **kwargs: any other parameters the dispatcher sends upon processing
        """
        if self._on_message:
            self._on_message(message)

    def accepts(self, manifest: Any) -> bool:
        """
        Determines whether it is able to handle a message or not
        """
        return True


class SingleDispatchConsumer(Consumer, SingleDispatch):
    """
    This class can consume events from a queue and pass them to a processor
    through the means of method overloading. Provides a default implementation as well for
    the accepts method
    """

    def process(self, message: Any, **kwargs: Any) -> None:
        self._process(message)

    @singledispatch
    def _process(self, message: Any) -> None:
        """Event should be an instance of DomainEvent"""
        pass

    def accepts(self, message: Any) -> bool:
        accepted_types = filter(lambda t: t is not object, self._process.registry)
        return any(isinstance(message, t) for t in accepted_types)


consumer = SingleDispatchConsumer._process.register
