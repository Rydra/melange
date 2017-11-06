import logging
import threading

from melange.domain_event_bus.domain_event import DomainEvent
from melange.domain_event_bus.domain_subscriber import DomainSubscriber
from melange.infrastructure.singleton import Singleton


@Singleton
class DomainEventBus:
    thread_local = threading.local()

    def __init__(self):
        self.thread_local.subscribers = []
        self.thread_local.publishing = False

    def publish(self, event):
        if self.thread_local.publishing:
            return

        if not isinstance(event, DomainEvent):
            logging.error('Invalid data passed. You must pass an event instance')
            return

        self.thread_local.publishing = True
        self._publish_synchronous(event)
        self.thread_local.publishing = False

    def reset(self):
        val = getattr(self.thread_local, 'publishing', None)
        if val is None:
            val = False
            self.thread_local.publishing = False

        if not val:
            self.thread_local.subscribers = []

    def subscribe(self, subscriber):

        if not isinstance(subscriber, DomainSubscriber):
            return False

        if subscriber not in self.thread_local.subscribers:
            self.thread_local.subscribers.append(subscriber)

    def _publish_synchronous(self, event):
        subscribers = self._get_subscribers(event)

        for subscr in subscribers:
            try:
                subscr.process(event)
            except Exception as e:
                logging.error(e)

    def _get_subscribers(self, event):
        return [subscriber for subscriber in self.thread_local.subscribers if subscriber.accepts(event)]

    def get_publishing(self):
        val = getattr(self.thread_local, 'publishing', None)
        if val is None:
            self.thread_local.publishing = False

        return self.thread_local.publishing
