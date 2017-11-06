import logging
from atexit import register
from queue import Queue, Empty
from threading import Lock, Thread
from time import time
from zlib import crc32

from melange.aws.eventmessage import EventMessage
from melange.aws.exchange_listener import ExchangeListener

MAX_TOPIC_INDEX = 16  # Must be power of 2
DEFAULT_NUM_THREADS = 8
MIN_NUM_THREADS = 1
MAX_NUM_THREADS = 128
MAXIMUM_QUEUE_LENGTH = 25600


def compute_crc32(data):
    strbytes = bytes(data, encoding='UTF-8')
    return crc32(strbytes)


class AsynchronousEventBus(Thread):
    def __init__(self, max_queued_event=10000, subscribers_thread_safe=True):
        """
        Creates an domain_event_bus object

        :param max_queued_event:  total number of un-ordered events queued.
        :type max_queued_event: int
        :param num_threads:  number of threads to process the queued event by calling the
                                corresponding subscribers.
        :type num_threads: int
        :param subscribers_thread_safe:  if the subscribers can be invoked for processing multiple
                                         events simultaneously.
        :type subscribers_thread_safe: bool
        """

        super().__init__()
        self.max_queued_event = max_queued_event
        register(self.shutdown)
        self.subscribers_thread_safe = subscribers_thread_safe
        self.topics = MAX_TOPIC_INDEX * [{}]

        self.consumers = {}
        self.consumers_lock = Lock()
        self.shutdown_lock = Lock()
        self.subscriber_locks = {}
        self.keep_running = True
        self.stop_time = 0

        self.index_locks = [Lock()] * MAX_TOPIC_INDEX

        self.event_queues = {}

        self.start()

    def publish(self, event, topic):

        if not isinstance(event, EventMessage):
            logging.error('Invalid data passed. You must pass an event instance')
            return False
        if not self.keep_running:
            return False

        self._init_topic(topic)
        self.event_queues[topic].put(event)

        return True

    def subscribe(self, subscriber):

        if not isinstance(subscriber, ExchangeListener):
            return False

        topic = subscriber.get_topic()

        self._init_topic(topic)

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

            if not self.subscribers_thread_safe and subscriber not in self.subscriber_locks:
                self.subscriber_locks[subscriber] = Lock()

    def unsubscribe(self, subscriber):

        with self.consumers_lock:
            subscribed_topics = None
            if subscriber in self.consumers:
                subscribed_topics = self.consumers[subscriber]
                del self.consumers[subscriber]
            if self.subscribers_thread_safe and (subscriber in self.subscriber_locks):
                del self.subscriber_locks[subscriber]

            for topic in subscribed_topics:
                indexval = self._get_topic_index(topic)
                with self.index_locks[indexval]:
                    if (topic in self.topics[indexval]) \
                            and (subscriber in self.topics[indexval][topic]):
                        self.topics[indexval][topic].remove(subscriber)
                        if len(self.topics[indexval][topic]) == 0:
                            del self.topics[indexval][topic]

    def is_subscribed(self, subscriber, topic):
        if not isinstance(subscriber, ExchangeListener):
            logging.error('Invalid object passed')
            return False

        indexval = self._get_topic_index(topic)
        with self.index_locks[indexval]:
            return topic in self.topics[indexval] and subscriber in self.topics[indexval][topic]

    def run(self):

        while not self._thread_should_end():
            for topic in self.event_queues:
                event = self._get_next_event(topic)
                if event is not None:
                    self._process_event(event, topic)

    def _init_topic(self, topic):
        if topic not in self.event_queues:
            self.event_queues[topic] = Queue(self.max_queued_event)

    def _get_subscribers(self, topic):
        indexval = self._get_topic_index(topic)
        with self.index_locks[indexval]:
            return self.topics[indexval][topic][:] if topic in self.topics[indexval] else []

    def _get_topic_index(self, topic):
        return compute_crc32(topic) & (MAX_TOPIC_INDEX - 1)

    def _get_next_event(self, topic):

        try:
            event = self.event_queues[topic].get(timeout=0.1)
        except Empty:
            return None
        except Exception as e:
            logging.error(e)
            return None

        self.event_queues[topic].task_done()

        return event

    def _process_event(self, event, topic):
        for subscriber in self._get_subscribers(topic):

            if not subscriber.accepts(event):
                continue

            lock = None
            if not self.subscribers_thread_safe:
                try:
                    lock = self.subscriber_locks[subscriber]
                except KeyError as e:
                    logging.error(e)
                    continue

            if lock is not None:
                lock.acquire()

            try:
                subscriber.process(event)
            except Exception as e:
                logging.error(e)

            if lock is not None:
                lock.release()

    def _thread_should_end(self):
        return self.stop_time > 0 and time() < self.stop_time

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
