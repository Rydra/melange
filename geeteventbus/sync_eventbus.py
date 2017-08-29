from atexit import register
from threading import Lock
import logging
from zlib import crc32
from geeteventbus.event import Event
from geeteventbus.subscriber import Subscriber

MAX_TOPIC_INDEX = 16  # Must be power of 2
DEFAULT_EXECUTOR_COUNT = 8
MIN_EXECUTOR_COUNT = 1
MAX_EXECUTOR_COUNT = 128
MAXIMUM_QUEUE_LENGTH = 25600
MINIMUM_QUEUE_LENGTH = 16


def get_crc32(data):
    '''Returns the crc32 value of the input string. '''
    strbytes = bytes(data, encoding='UTF-8')
    return crc32(strbytes)



class SynchronousEventBus:
    def __init__(self):

        register(self.shutdown)
        self.topics = MAX_TOPIC_INDEX * [{}]
        self.consumers = {}  # Only used to quickly register and unregister consumers
        self.consumers_lock = Lock()

        self.index_locks = [Lock()] * MAX_TOPIC_INDEX

    def post(self, eventobj):

        if not isinstance(eventobj, Event):
            logging.error('Invalid data passed. You must pass an event instance')
            return False

        self._post_synchronous(eventobj)
        return True

    def register_consumer_topics(self, consumer, topic_list):

        for topic in topic_list:
            self.register_consumer(consumer, topic)

    def register_consumer(self, consumer, topic):

        if not isinstance(consumer, Subscriber):
            return False

        indexval = self._get_topic_index(topic)
        with self.consumers_lock:
            with self.index_locks[indexval]:
                if topic not in self.topics[indexval]:
                    self.topics[indexval][topic] = [consumer]
                elif consumer not in self.topics[indexval][topic]:
                    self.topics[indexval][topic].append(consumer)

            if consumer not in self.consumers:
                self.consumers[consumer] = [topic]
            elif topic not in self.consumers[consumer]:
                self.consumers[consumer].append(topic)

    def unregister_consumer(self, consumer):

        with self.consumers_lock:
            subscribed_topics = None
            if consumer in self.consumers:
                subscribed_topics = self.consumers[consumer]
                del self.consumers[consumer]

            for topic in subscribed_topics:
                indexval = self._get_topic_index(topic)
                with self.index_locks[indexval]:
                    if (topic in self.topics[indexval]) and (consumer in
                                                                 self.topics[indexval][topic]):
                        self.topics[indexval][topic].remove(consumer)
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

    def _post_synchronous(self, eventobj):
        topic = eventobj.get_topic()
        subscribers = self._get_subscribers(topic)

        for subscr in subscribers:
            try:
                subscr.process(eventobj)
            except Exception as e:
                logging.error(e)

    def _get_subscribers(self, topic):
        indexval = self._get_topic_index(topic)
        with self.index_locks[indexval]:
            return self.topics[indexval][topic][:] if topic in self.topics[indexval] else []

    def _get_topic_index(self, topic):
        return get_crc32(topic) & (MAX_TOPIC_INDEX - 1)

    def shutdown(self):
        pass
