from atexit import register
from threading import Thread, Lock
from time import time

from melange.aws.message_consumer import MessageConsumer


class ThreadedMessageConsumer(Thread, MessageConsumer):
    def __init__(self, event_serializer, event_queue_name, topic_to_subscribe):

        MessageConsumer.__init__(self, event_serializer, event_queue_name, topic_to_subscribe)
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
