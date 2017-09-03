import logging
from atexit import register
from threading import Lock
from zlib import crc32

from melange.event import Event
from melange.subscriber import Subscriber

MAX_TOPIC_INDEX = 16  # Must be power of 2
DEFAULT_EXECUTOR_COUNT = 8
MIN_EXECUTOR_COUNT = 1
MAX_EXECUTOR_COUNT = 128
MAXIMUM_QUEUE_LENGTH = 25600
MINIMUM_QUEUE_LENGTH = 16


def compute_crc32(data):
    strbytes = bytes(data, encoding='UTF-8')
    return crc32(strbytes)


class SynchronousEventBus:
    def __init__(self):

        register(self.shutdown)
        self.topics = MAX_TOPIC_INDEX * [{}]
        self.consumers = {}  # Only used to quickly register and unregister consumers
        self.consumers_lock = Lock()

        self.index_locks = [Lock()] * MAX_TOPIC_INDEX

    def publish(self, event, topic):

        if not isinstance(event, Event):
            logging.error('Invalid data passed. You must pass an event instance')
            return False

        self._publish_synchronous(event, topic)
        return True

    def subscribe(self, subscriber):

        if not isinstance(subscriber, Subscriber):
            return False

        topic = subscriber.get_topic()

        indexval = self._get_topic_index(topic)
        with self.consumers_lock:
            with self.index_locks[indexval]:
                if topic not in self.topics[indexval]:
                    self.topics[indexval][topic] = [subscriber]
                elif subscriber not in self.topics[indexval][topic]:
                    self.topics[indexval][topic].append(subscriber)

            if subscriber not in self.consumers:
                self.consumers[subscriber] = [topic]
            elif topic not in self.consumers[subscriber]:
                self.consumers[subscriber].append(topic)

    def unsubscribe(self, subscriber):

        with self.consumers_lock:
            subscribed_topics = None
            if subscriber in self.consumers:
                subscribed_topics = self.consumers[subscriber]
                del self.consumers[subscriber]

            for topic in subscribed_topics:
                indexval = self._get_topic_index(topic)
                with self.index_locks[indexval]:
                    if (topic in self.topics[indexval]) and (subscriber in self.topics[indexval][topic]):
                        self.topics[indexval][topic].remove(subscriber)
                        if len(self.topics[indexval][topic]) == 0:
                            del self.topics[indexval][topic]

    def is_subscribed(self, consumer, topic):

        if not isinstance(consumer, Subscriber):
            logging.error('Invalid object passed')
            return False

        indexval = self._get_topic_index(topic)
        with self.index_locks[indexval]:
            if topic not in self.topics[indexval]:
                return False
            return consumer in self.topics[indexval][topic]

    def _publish_synchronous(self, event, topic):
        subscribers = self._get_subscribers(topic)

        for subscr in subscribers:
            try:
                if subscr.accepts(event):
                    subscr.process(event)
            except Exception as e:
                logging.error(e)

    def _get_subscribers(self, topic):
        indexval = self._get_topic_index(topic)
        with self.index_locks[indexval]:
            return self.topics[indexval][topic][:] if topic in self.topics[indexval] else []

    def _get_topic_index(self, topic):
        return compute_crc32(topic) & (MAX_TOPIC_INDEX - 1)

    def shutdown(self):
        pass
