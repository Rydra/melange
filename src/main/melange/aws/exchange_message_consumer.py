import json
import logging
from atexit import register
from threading import Thread, Lock
from time import time

from melange.aws.event_serializer import EventSerializer
from melange.aws.eventmessage import EventMessage
from melange.aws.exchange_listener import ExchangeListener
from melange.aws.messaging_manager import MessagingManager


class ExchangeMessageConsumer:
    def __init__(self, event_queue_name, topic_to_subscribe):
        self._exchange_listeners = []
        topic = MessagingManager.declare_topic(topic_to_subscribe)
        self._event_queue, _ = MessagingManager.declare_queue(event_queue_name, topic)

    def subscribe(self, exchange_listener):
        if not isinstance(exchange_listener, ExchangeListener):
            return False

        if exchange_listener not in self._exchange_listeners:
            self._exchange_listeners.append(exchange_listener)

    def unsubscribe(self, exchange_listener):
        if exchange_listener in self._exchange_listeners:
            self._exchange_listeners.remove(exchange_listener)

    def consume_event(self):
        self._poll_next_event()

    def _get_subscribers(self, event_type_name):
        return [listener for listener in self._exchange_listeners if listener.accepts(event_type_name)]

    def _poll_next_event(self):

        messages = self._event_queue.receive_messages(MaxNumberOfMessages=1, VisibilityTimeout=100,
                                                      WaitTimeSeconds=10, AttributeNames=['All'])

        for message in messages:
            try:
                self._process_message(message)
            except Exception as e:
                logging.error(e)

    def _process_message(self, message):
        body = message.body
        message_content = json.loads(body)
        if 'Message' in message_content:
            content = json.loads(message_content['Message'])
        else:
            content = message_content

        if 'event_type_name' not in content:
            return True

        try:
            event = EventSerializer.instance().deserialize(content)
        except ValueError:
            event = content

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
            message.delete()


class ThreadedExchangeMessageConsumer(Thread, ExchangeMessageConsumer):
    def __init__(self, event_queue_name, topic_to_subscribe):

        ExchangeMessageConsumer.__init__(self, event_queue_name, topic_to_subscribe)
        Thread.__init__(self)

        register(self.shutdown)

        self.keep_running = True
        self.stop_time = 0
        self.shutdown_lock = Lock()

    def run(self):

        while not self._thread_should_end():
            self.consume_event()

    def _thread_should_end(self):
        return 0 < self.stop_time < time()

    def shutdown(self):
        """
        Stops the event bus. The event bus will stop all its executor threads.
        It will try to flush out already queued events by calling the subscribers
        of the events. This flush wait time is 2 seconds.
        """

        with self.shutdown_lock:
            if not self.keep_running:
                return
            self.keep_running = False
        self.stop_time = time() + 2

        self.join()
