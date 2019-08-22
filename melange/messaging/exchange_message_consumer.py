import logging

from melange.messaging import EventMessage
from melange.messaging import EventSerializer
from melange.messaging import ExchangeListener
from .driver_manager import DriverManager


logger = logging.getLogger(__name__)


class ExchangeMessageYielder:
    def __init__(self, event_queue_name, *topics_to_subscribe, dead_letter_queue_name=None, driver=None, **kwargs):
        self._driver = driver or DriverManager.instance().get_driver()
        self._event_queue_name = event_queue_name
        self._topics_to_subscribe = topics_to_subscribe
        self._dead_letter_queue_name = dead_letter_queue_name

        self._topics = [self._driver.declare_topic(t) for t in self._topics_to_subscribe]
        self._event_queue, self._dead_letter_queue = self._driver.declare_queue(
            self._event_queue_name, *self._topics,
            dead_letter_queue_name=self._dead_letter_queue_name,
            filter_events=kwargs.get('filter_events'))

    def get_messages(self):
        event_queue = self._driver.get_queue(self._event_queue_name)

        while True:
            messages = self._driver.retrieve_messages(event_queue)

            for message in messages:
                if 'event_type_name' in message.content:
                    yield EventSerializer.instance().deserialize(message.content)

    def acknowledge(self, message):
        self._driver.acknowledge(message)


class ExchangeMessageConsumer:
    def __init__(self, event_queue_name, *topics_to_subscribe, dead_letter_queue_name=None, driver=None, **kwargs):
        self._exchange_listeners = []
        self._driver = driver or DriverManager.instance().get_driver()
        self._event_queue_name = event_queue_name
        self._topics_to_subscribe = topics_to_subscribe
        self._dead_letter_queue_name = dead_letter_queue_name

        self._topics = [self._driver.declare_topic(t) for t in self._topics_to_subscribe]
        self._event_queue, self._dead_letter_queue = self._driver.declare_queue(
            self._event_queue_name, *self._topics,
            dead_letter_queue_name=self._dead_letter_queue_name,
            filter_events=kwargs.get('filter_events'))

    def subscribe(self, exchange_listener):
        if not isinstance(exchange_listener, ExchangeListener):
            return False

        if exchange_listener not in self._exchange_listeners:
            self._exchange_listeners.append(exchange_listener)

    def unsubscribe(self, exchange_listener):
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

    def _get_subscribers(self, event_type_name):
        return [listener for listener in self._exchange_listeners if listener.accepts(event_type_name)]

    def _process_message(self, message):
        if 'event_type_name' not in message.content:
            # The message will be ignored but not deleted from the
            # queue. Let the dead letter queue handle it
            return True

        event = EventSerializer.instance().deserialize(message.content)
        event_type_name = event.event_type_name if isinstance(event, EventMessage) else event['event_type_name']
        subscribers = self._get_subscribers(event_type_name)

        successful = 0
        for subscr in subscribers:
            try:
                subscr.process_event(event, message_id=message.message_id)
                successful += 1
            except Exception as e:
                logger.exception(e)

        if successful == len(subscribers):
            self._driver.acknowledge(message)
