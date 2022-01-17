import logging
from typing import Any, Callable, List, Optional

from funcy import lmap
from methoddispatch import SingleDispatch, singledispatch

from melange.backends.backend_manager import BackendManager
from melange.backends.interfaces import Message, MessagingBackend
from melange.infrastructure.cache import Cache, DedupCache
from melange.serializers.interfaces import MessageSerializer
from melange.utils import get_fully_qualified_name

logger = logging.getLogger(__name__)


class Consumer:
    def process(self, obj: Any, **kwargs: Any) -> None:
        pass

    def accepts(self, manifest: Optional[str]) -> bool:
        return True


class SingleDispatchConsumer(Consumer, SingleDispatch):
    """
    This class can consume events from a queue and pass them to a processor
    """

    def process(self, obj: Any, **kwargs: Any) -> None:
        self._process(obj)

    @singledispatch
    def _process(self, obj: Any) -> None:
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


class SimpleConsumerHandler:
    """
    Handles the retrieval of messages from a queue and
    dispatches the messages to the consumer
    """

    def __init__(
        self,
        consumer: Consumer,
        message_serializer: MessageSerializer,
        cache: Optional[DedupCache] = None,
        backend: Optional[MessagingBackend] = None,
        always_ack: bool = False,
    ):
        self.consumer = consumer
        self.message_serializer = message_serializer
        self._backend = backend or BackendManager().get_backend()
        self.cache: DedupCache = cache or Cache()
        self.always_ack = always_ack

    def consume_loop(
        self,
        queue_name: str,
        on_exception: Optional[Callable[[Exception], None]] = None,
        after_consume: Optional[Callable[[], None]] = None,
    ) -> None:
        while True:
            try:
                self.consume_event(queue_name)
            except Exception as e:
                logger.exception(e)
                if on_exception:
                    on_exception(e)
            finally:
                if after_consume:
                    after_consume()

    def consume_event(self, queue_name: str) -> None:
        event_queue = self._backend.get_queue(queue_name)

        messages = self._backend.retrieve_messages(event_queue)

        for message in messages:
            try:
                self._dispatch_message(message)
            except Exception as e:
                logger.exception(e)

    def _dispatch_message(self, message: Message) -> None:
        manifest = message.get_message_manifest()
        message_data = self.message_serializer.deserialize(
            message.content, manifest=manifest
        )

        successful = False
        try:
            # Store into the cache
            message_key = get_fully_qualified_name(self) + "." + message.message_id

            if message_key in self.cache:
                logger.info("detected a duplicated message, ignoring")
            else:
                self.consumer.process(message_data, message_id=message.message_id)
                successful = True
                self.cache.store(message_key, message_key)
        except Exception as e:
            logger.exception(e)

        if self.always_ack or successful:
            self._backend.acknowledge(message)
