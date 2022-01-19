import logging
from typing import Callable, List, Optional

from melange.backends.backend_manager import BackendManager
from melange.backends.interfaces import Message, MessagingBackend
from melange.consumers import Consumer
from melange.infrastructure.cache import Cache, DedupCache
from melange.serializers.interfaces import MessageSerializer
from melange.utils import get_fully_qualified_name

# TODO: Clear code duplication between the dispatcher and the handler. Fix.

logger = logging.getLogger(__name__)


class ConsumerDispatcher:
    """
    Dispatches messages read by the consume event to the
    consumers that accept the message of that type
    """

    def __init__(
        self,
        message_serializer: MessageSerializer,
        cache: Optional[DedupCache] = None,
        backend: Optional[MessagingBackend] = None,
    ) -> None:
        self._exchange_listeners: List[Consumer] = []
        self.message_serializer = message_serializer
        self._backend = backend or BackendManager().get_backend()
        self.cache: DedupCache = cache or Cache()

    def subscribe(self, consumer: Consumer) -> None:
        if not isinstance(consumer, Consumer):
            return None

        if consumer not in self._exchange_listeners:
            self._exchange_listeners.append(consumer)

    def unsubscribe(self, consumer: Consumer) -> None:
        if consumer in self._exchange_listeners:
            self._exchange_listeners.remove(consumer)

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

    def _get_consumers(self, manifest: Optional[str]) -> List[Consumer]:
        return [
            listener
            for listener in self._exchange_listeners
            if listener.accepts(manifest)
        ]

    def _dispatch_message(self, message: Message) -> None:
        manifest = message.get_message_manifest()
        message_data = self.message_serializer.deserialize(
            message.content, manifest=manifest
        )
        subscribers = self._get_consumers(manifest)

        successful = 0
        for subscr in subscribers:
            try:
                # Store into the cache
                message_key = (
                    get_fully_qualified_name(subscr) + "." + message.message_id
                )

                if message_key in self.cache:
                    logger.info("detected a duplicated message, ignoring")
                else:
                    subscr.process(message_data, message_id=message.message_id)
                    successful += 1
                    self.cache.store(message_key, message_key)
            except Exception as e:
                logger.exception(e)

        if successful == len(subscribers):
            self._backend.acknowledge(message)


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
