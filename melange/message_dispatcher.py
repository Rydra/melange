import logging
from typing import Any, Callable, Iterable, List, Optional

from melange.backends.backend_manager import BackendManager
from melange.backends.interfaces import Message, MessagingBackend
from melange.consumer import SingleDispatchConsumer
from melange.infrastructure.cache import Cache, DedupCache
from melange.serializers.interfaces import MessageSerializer
from melange.utils import get_fully_qualified_name

logger = logging.getLogger(__name__)


class ExchangeMessageYielder:
    def __init__(
        self,
        event_queue_name: str,
        message_serializer: MessageSerializer,
        *topics_to_subscribe: str,
        dead_letter_queue_name: Optional[str] = None,
        backend: Optional[MessagingBackend] = None,
        **kwargs: Any
    ):
        self._backend = backend or BackendManager().get_backend()
        self.message_serializer = message_serializer
        self._event_queue_name = event_queue_name
        self._topics_to_subscribe = topics_to_subscribe
        self._dead_letter_queue_name = dead_letter_queue_name

        self._topics = [
            self._backend.declare_topic(t) for t in self._topics_to_subscribe
        ]
        self._event_queue, self._dead_letter_queue = self._backend.declare_queue(
            self._event_queue_name,
            *self._topics,
            dead_letter_queue_name=self._dead_letter_queue_name,
            filter_events=kwargs.get("filter_events")
        )

    def get_messages(self) -> Iterable[str]:
        event_queue = self._backend.get_queue(self._event_queue_name)

        while True:
            messages = self._backend.retrieve_messages(event_queue)

            for message in messages:
                if "event_type_name" in message.content:
                    yield self.message_serializer.deserialize(message.content)

    def acknowledge(self, message: Message) -> None:
        self._backend.acknowledge(message)


class ExchangeMessageDispatcher:
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
        self._exchange_listeners: List[SingleDispatchConsumer] = []
        self.message_serializer = message_serializer
        self._backend = backend or BackendManager().get_backend()
        self.cache: DedupCache = cache or Cache()

    def subscribe(self, consumer: SingleDispatchConsumer) -> None:
        if not isinstance(consumer, SingleDispatchConsumer):
            return None

        if consumer not in self._exchange_listeners:
            self._exchange_listeners.append(consumer)

    def unsubscribe(self, consumer: SingleDispatchConsumer) -> None:
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

    def _get_consumers(self, manifest: Optional[str]) -> List[SingleDispatchConsumer]:
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
