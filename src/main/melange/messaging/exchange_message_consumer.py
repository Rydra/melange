import logging

from melange.messaging import EventMessage
from melange.messaging import EventSerializer
from melange.messaging import ExchangeListener
from .driver_manager import DriverManager


class ExchangeMessageConsumer:
    def __init__(self, event_queue_name, topic_to_subscribe=None, dead_letter_queue_name=None, driver=None):
        self._exchange_listeners = []
        self._driver = driver or DriverManager.instance().get_driver()
        self._topic = self._driver.declare_topic(topic_to_subscribe) if topic_to_subscribe else None
        self._event_queue, self._dead_letter_queue = self._driver.declare_queue(event_queue_name,
                                                                                self._topic,
                                                                                dead_letter_queue_name)

    def subscribe(self, exchange_listener):
        if not isinstance(exchange_listener, ExchangeListener):
            return False

        if exchange_listener not in self._exchange_listeners:
            self._exchange_listeners.append(exchange_listener)

    def unsubscribe(self, exchange_listener):
        if exchange_listener in self._exchange_listeners:
            self._exchange_listeners.remove(exchange_listener)

    def consume_event(self):
        messages = self._driver.retrieve_messages(self._event_queue)

        for message in messages:
            try:
                self._process_message(message)
            except Exception as e:
                logging.error(e)

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
                logging.error(e)

        if successful == len(subscribers):
            self._driver.acknowledge(message)
