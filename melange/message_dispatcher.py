import logging
from typing import Any, Callable, List, Optional

from melange.backends.backend_manager import BackendManager
from melange.backends.interfaces import MessagingBackend
from melange.consumers import Consumer
from melange.exceptions import SerializationError
from melange.infrastructure.cache import DeduplicationCache, NullCache
from melange.models import Message
from melange.serializers.registry import SerializerRegistry
from melange.utils import get_fully_qualified_name

# TODO: Clear code duplication between the dispatcher and the handler. Fix.

logger = logging.getLogger(__name__)


class MessageDispatcher:
    """
    The `MessageDispatcher` is responsible to start the message consumption loop
    to retrieve the available messages from the queue and dispatch them to the
    consumers.
    """

    def __init__(
        self,
        serializer_registry: SerializerRegistry,
        cache: Optional[DeduplicationCache] = None,
        backend: Optional[MessagingBackend] = None,
        always_ack: bool = False,
    ) -> None:
        self._consumers: List[Consumer] = []
        self.serializer_registry = serializer_registry
        self._backend = backend or BackendManager().get_default_backend()
        self.cache: DeduplicationCache = cache or NullCache()
        self.always_ack = always_ack

    def attach_consumer(self, consumer: Consumer) -> None:
        """
        Attaches a consumer to the dispatcher, so that it can receive messages
        Args:
            consumer: the consumer to attach
        """
        if consumer not in self._consumers:
            self._consumers.append(consumer)

    def unattach_consumer(self, consumer: Consumer) -> None:
        """
        Unattaches the consumer from the dispatcher, so that it will not receive messages anymore
        Args:
            consumer: the consumer to unattach
        """
        if consumer in self._consumers:
            self._consumers.remove(consumer)

    def consume_loop(
        self,
        queue_name: str,
        on_exception: Optional[Callable[[Exception], None]] = None,
        after_consume: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        Starts the consumption loop on the queue `queue_name`
        Args:
            queue_name: The queue to poll for new messages
            on_exception: If there is any exception, the exception
                will be passed to this callback
            after_consume: After consuming a batch of events,
                invoke this callback
        """
        self.consume_event(queue_name, on_exception, after_consume)

    def consume_event(
        self,
        queue_name: str,
        on_exception: Optional[Callable[[Exception], None]] = None,
        after_consume: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        Consumes events on the queue `queue_name`
        """
        event_queue = self._backend.get_queue(queue_name)

        messages = self._backend.yield_messages(event_queue)
        for message in messages:
            try:
                self._dispatch_message(message)
            except Exception as e:
                logger.exception(e)
                if on_exception:
                    on_exception(e)
            finally:
                if after_consume:
                    after_consume()

    def _get_consumers(self, message_data: Any) -> List[Consumer]:
        return [
            consumer for consumer in self._consumers if consumer.accepts(message_data)
        ]

    def _dispatch_message(self, message: Message) -> None:
        manifest = message.get_message_manifest()

        # If the message cannot be deserialized, just ignore it.
        # ACK it anyway to avoid hanging on the same message over an over again
        try:
            if message.serializer_id is not None:
                message_data = self.serializer_registry.deserialize_with_serializerid(
                    message.content, message.serializer_id, manifest=manifest
                )
            else:
                # TODO: If no serializerid is supplied, at least we need to grab some
                # clue in the message to know which serializer must be used.
                # for now, rely on the default.
                message_data = self.serializer_registry.deserialize_with_class(
                    message.content, object, manifest=manifest
                )
        except SerializationError as e:
            logger.error(e)
            self._backend.acknowledge(message)
            return

        consumers = self._get_consumers(message_data)

        successful = 0
        for consumer in consumers:
            try:
                # Store into the cache
                message_key = (
                    f"{get_fully_qualified_name(consumer)}.{message.message_id}"
                )

                if message_key in self.cache:
                    logger.info("detected a duplicated message, ignoring")
                else:
                    consumer.process(message_data, message_id=message.message_id)
                    successful += 1
                    self.cache.store(message_key, message_key)
            except Exception as e:
                logger.exception(e)

        if self.always_ack or successful == len(consumers):
            self._backend.acknowledge(message)


class SimpleMessageDispatcher(MessageDispatcher):
    """
    Handles the retrieval of messages from a queue and
    dispatches the messages to a single consumer. A simpler version
    of the `MessageDispatcher`
    """

    def __init__(
        self,
        consumer: Consumer,
        serializer_registry: SerializerRegistry,
        cache: Optional[DeduplicationCache] = None,
        backend: Optional[MessagingBackend] = None,
        always_ack: bool = False,
    ):
        super().__init__(serializer_registry, cache, backend, always_ack)
        self.attach_consumer(consumer)
