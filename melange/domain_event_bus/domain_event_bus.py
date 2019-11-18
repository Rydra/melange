import logging
import threading

from .domain_event import DomainEvent
from .domain_subscriber import DomainEventHandler
from melange.infrastructure import Singleton


logger = logging.getLogger(__name__)


@Singleton
class DomainEventBus:
    thread_local = threading.local()

    def __init__(self):
        self.thread_local.subscribers = []
        self.thread_local.publishing = False
        self.thread_local.keep_publishing = False

    def is_publishing(self):
        return getattr(self.thread_local, 'publishing', False)

    def keep_publishing(self):
        self.thread_local.keep_publishing = True

    def should_keep_publishing(self):
        return getattr(self.thread_local, 'keep_publishing', False)

    def publish(self, event, **kwargs):
        if self.is_publishing() and not self.should_keep_publishing():
            return

        if not isinstance(event, DomainEvent):
            logger.error('Invalid data passed. You must pass an event instance')
            return

        self.thread_local.publishing = True
        self._publish_synchronous(event, **kwargs)
        self.thread_local.publishing = False

    def reset(self):
        val = getattr(self.thread_local, 'publishing', None)
        if val is None:
            val = False
            self.thread_local.publishing = False
            self.thread_local.keep_publishing = False

        if not self.is_publishing():
            self.thread_local.subscribers = []

    def subscribe(self, subscriber):
        if self.is_publishing() or not isinstance(subscriber, DomainEventHandler):
            return False

        if subscriber not in self.thread_local.subscribers:
            self.thread_local.subscribers.append(subscriber)

    def _publish_synchronous(self, event, **kwargs):
        subscribers = self._get_subscribers(event)

        for subscr in subscribers:
            try:
                event._meta = kwargs
                subscr.process(event)
            except Exception as e:
                logger.exception(e)

    def _get_subscribers(self, event):
        return [subscriber for subscriber in self.thread_local.subscribers if subscriber.accepts(event)]

    def get_publishing(self):
        val = getattr(self.thread_local, 'publishing', None)
        if val is None:
            self.thread_local.publishing = False

        return self.thread_local.publishing
