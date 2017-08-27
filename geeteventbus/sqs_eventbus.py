from atexit import register
from time import time
from threading import Lock, Thread, current_thread
import logging
import sys
from zlib import crc32
from geeteventbus.event import event
from geeteventbus.sqs_queue import SQSQueue
from geeteventbus.subscriber import subscriber
from queue import Queue, Empty
import boto3

MAX_TOPIC_INDEX = 16  # Must be power of 2
DEFAULT_EXECUTOR_COUNT = 8
MIN_EXECUTOR_COUNT = 1
MAX_EXECUTOR_COUNT = 128
MAXIMUM_QUEUE_LENGTH = 25600


def get_crc32(data):
    '''Returns the crc32 value of the input string. '''

    strbytes = bytes(data, encoding='UTF-8')
    return crc32(strbytes)

class SQSEventBus:
    def __init__(self, subscribers_thread_safe=True):
        '''
        Creates an eventbus object

        :param max_queued_event:  total number of un-ordered events queued.
        :type max_queued_event: int
        :param executor_count:  number of threads to process the queued event by calling the
                                corresponding subscribers.
        :type executor_count: int
        :param subscribers_thread_safe:  if the subscribers can be invoked for processing multiple
                                         events simultaneously.
        :type subscribers_thread_safe: bool
        '''

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

        self.event_queue = SQSQueue()

        name = 'executor_thread_main'
        self.event_thread = Thread(target=self, name=name)

        self.event_thread.start()

    def post(self, eventobj):

        if not isinstance(eventobj, event):
            logging.error('Invalid data passed. You must pass an event instance')
            return False
        if not self.keep_running:
            return False

        queue = self._choose_queue(eventobj)
        queue.put(eventobj)

        return True

    def register_consumer_topics(self, consumer, topic_list):

        for topic in topic_list:
            self.register_consumer(consumer, topic)

    def register_consumer(self, consumer, topic):

        if not isinstance(consumer, subscriber):
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

            if not self.subscribers_thread_safe and consumer not in self.subscriber_locks:
                self.subscriber_locks[consumer] = Lock()

    def unregister_consumer(self, consumer):
        '''
        Unregister the consumer.

        The consumer will no longer receieve any event to process for any topic

        :param conumer: the subscriber object to unregister
        '''

        with self.consumers_lock:
            subscribed_topics = None
            if consumer in self.consumers:
                subscribed_topics = self.consumers[consumer]
                del self.consumers[consumer]
            if self.subscribers_thread_safe and (consumer in self.subscriber_locks):
                del self.subscriber_locks[consumer]

            for topic in subscribed_topics:
                indexval = self._get_topic_index(topic)
                with self.index_locks[indexval]:
                    if (topic in self.topics[indexval]) \
                            and (consumer in self.topics[indexval][topic]):
                        self.topics[indexval][topic].remove(consumer)
                        if len(self.topics[indexval][topic]) == 0:
                            del self.topics[indexval][topic]

    def is_subscribed(self, consumer, topic):
        if not isinstance(consumer, subscriber):
            logging.error('Invalid object passed')
            return False

        indexval = self._get_topic_index(topic)
        with self.index_locks[indexval]:
            return topic in self.topics[indexval] and consumer in self.topics[indexval][topic]

    def __call__(self):

        while not self._thread_should_end():
            eventobj = self._get_next_event()
            if eventobj is not None:
                self._process_event(eventobj)

    def _choose_queue(self, eventobj):
        '''
        If an event requires a determined order, in order to ensure it we add it
        to a proper queue in the same thread. Otherwise just return the default event queue
        '''

        return self.event_queue

    def _get_subscribers(self, topic):
        indexval = self._get_topic_index(topic)
        with self.index_locks[indexval]:
            return self.topics[indexval][topic][:] if topic in self.topics[indexval] else []

    def _get_topic_index(self, topic):
        return get_crc32(topic) & (MAX_TOPIC_INDEX - 1)

    def _get_next_event(self):

        queue, timeout = self._choose_queue_to_pull()
        try:
            eventobj = queue.get(timeout=timeout)
        except Empty:
            return None
        except Exception as e:
            logging.error(e)
            return None

        queue.task_done()

        return eventobj  # No harm, announce task done upfront

    def _choose_queue_to_pull(self):

        return self.event_queue, 0

    def _process_event(self, eventobj):
        for subscr in self._get_subscribers(eventobj.get_topic()):
            lock = None
            if not self.subscribers_thread_safe:
                try:
                    lock = self.subscriber_locks[subscr]
                except KeyError as e:
                    logging.error(e)
                    continue

            if lock is not None:
                lock.acquire()

            try:
                subscr.process(eventobj)
            except Exception as e:
                logging.error(e)

            if lock is not None:
                lock.release()

    def _thread_should_end(self):
        return self.stop_time > 0 and time() < self.stop_time

    def shutdown(self):
        '''
        Stops the event bus. The event bus will stop all its executor threads.
        It will try to flush out already queued events by calling the subscribers
        of the events. This flush wait time is 2 seconds.
        '''

        with self.shutdown_lock:
            if not self.keep_running:
                return
            self.keep_running = False
        self.stop_time = time() + 2

        self.event_thread.join()
