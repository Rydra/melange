import logging
from typing import List

from melange.drivers.driver_manager import DriverManager
from melange.event_serializer import MessageSerializer
from melange.exchange_listener import ExchangeListener
from melange.infrastructure.cache import DedupCache, Cache
from melange.drivers.interfaces import MessagingDriver, Message
from melange.utils import get_fully_qualified_name

logger = logging.getLogger(__name__)


class ExchangeMessageYielder:
    def __init__(
        self,
        event_queue_name,
        message_serializer: MessageSerializer,
        *topics_to_subscribe,
        dead_letter_queue_name=None,
        driver=None,
        **kwargs
    ):
        self._driver = driver or DriverManager().get_driver()
        self.message_serializer = message_serializer
        self._event_queue_name = event_queue_name
        self._topics_to_subscribe = topics_to_subscribe
        self._dead_letter_queue_name = dead_letter_queue_name

        self._topics = [
            self._driver.declare_topic(t) for t in self._topics_to_subscribe
        ]
        self._event_queue, self._dead_letter_queue = self._driver.declare_queue(
            self._event_queue_name,
            *self._topics,
            dead_letter_queue_name=self._dead_letter_queue_name,
            filter_events=kwargs.get("filter_events")
        )

    def get_messages(self):
        event_queue = self._driver.get_queue(self._event_queue_name)

        while True:
            messages = self._driver.retrieve_messages(event_queue)

            for message in messages:
                if "event_type_name" in message.content:
                    yield self.message_serializer.deserialize(message.content)

    def acknowledge(self, message):
        self._driver.acknowledge(message)


class ExchangeMessageConsumer:
    def __init__(
        self,
        event_queue_name: str,
        message_serializer: MessageSerializer,
        *topic_names_to_subscribe: str,
        dead_letter_queue_name: str = None,
        cache: DedupCache = None,
        driver: MessagingDriver = None,
        **kwargs
    ):
        self._exchange_listeners: List[ExchangeListener] = []
        self.message_serializer = message_serializer
        self._driver = driver or DriverManager().get_driver()
        self._event_queue_name = event_queue_name
        self._topics_to_subscribe = topic_names_to_subscribe
        self._dead_letter_queue_name = dead_letter_queue_name
        self.cache = cache or Cache()

        self._topics = [
            self._driver.declare_topic(t) for t in self._topics_to_subscribe
        ]
        self._event_queue, self._dead_letter_queue = self._driver.declare_queue(
            self._event_queue_name,
            *self._topics,
            dead_letter_queue_name=self._dead_letter_queue_name,
            filter_events=kwargs.get("filter_events")
        )

    def subscribe(self, exchange_listener: ExchangeListener) -> None:
        if not isinstance(exchange_listener, ExchangeListener):
            return None

        if exchange_listener not in self._exchange_listeners:
            self._exchange_listeners.append(exchange_listener)

    def unsubscribe(self, exchange_listener: ExchangeListener) -> None:
        if exchange_listener in self._exchange_listeners:
            self._exchange_listeners.remove(exchange_listener)

    def consume_event(self):
        event_queue = self._driver.get_queue(self._event_queue_name)

        messages = self._driver.retrieve_messages(event_queue)

        for message in messages:
            try:
                self._process_message(message)
            except Exception as e:
                logger.exception(e)

    def _get_subscribers(self, manifest: str):
        return [
            listener
            for listener in self._exchange_listeners
            if listener.accepts(manifest)
        ]

    def _process_message(self, message: Message):
        manifest = message.get_message_manifest()
        message_data = self.message_serializer.deserialize(
            message.content, manifest=manifest
        )
        subscribers = self._get_subscribers(manifest)

        successful = 0
        for subscr in subscribers:
            try:
                # Store into the cache
                message_listener_key = (
                    get_fully_qualified_name(subscr) + "." + message.message_id
                )

                if message_listener_key in self.cache:
                    logger.info("detected a duplicated message, ignoring")
                else:
                    subscr.process(message_data, message_id=message.message_id)
                    successful += 1
                    self.cache.store(message_listener_key, message_listener_key)
            except Exception as e:
                logger.exception(e)

        if successful == len(subscribers):
            self._driver.acknowledge(message)
