from __future__ import absolute_import

__title__ = "melange"
from melange.__version__ import __version__  # noqa

__author__ = "David Jiménez"
__license__ = "Apache License 2.0"
__copyright__ = "Copyright 2022 David Jiménez, David Arthur, and Contributors"

from melange.backends.factory import MessagingBackendFactory
from melange.consumers import Consumer, SingleDispatchConsumer, consumer
from melange.message_dispatcher import MessageDispatcher, SimpleMessageDispatcher
from melange.publishers import QueuePublisher, TopicPublisher

__all__ = [
    "TopicPublisher",
    "QueuePublisher",
    "MessageDispatcher",
    "SimpleMessageDispatcher",
    "Consumer",
    "SingleDispatchConsumer",
    "consumer",
    "MessagingBackendFactory",
]
