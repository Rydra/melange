import logging
import uuid

from .event_serializer import EventMessage
from .event_serializer import EventSerializer
from .driver_manager import DriverManager


logger = logging.getLogger(__name__)


class ExchangeMessagePublisher:
    def __init__(self, topic, driver=None):
        self._driver = driver or DriverManager.instance().get_driver()
        self._topic_name = topic

    def init(self):
        self._topic = self._driver.declare_topic(self._topic_name)

    def publish(self, event, event_type_name=None):
        if not isinstance(event, EventMessage) and not isinstance(event, dict):
            logger.error('Invalid data passed. You must pass an event instance or a dict')
            raise Exception('Invalid data passed. You must pass an event instance or a dict')

        if not event_type_name and (isinstance(event, dict) and 'event_type_name' not in event):
            raise Exception('When passing an event as a dict it has to include at least the event_type_name property')

        if event_type_name and isinstance(event, dict):
            event['event_type_name'] = event_type_name

        content = EventSerializer.instance().serialize(event)

        if not event_type_name:
            event_type_name = event.event_type_name if isinstance(event, EventMessage) else event['event_type_name']

        self.init()
        self._driver.publish(content, self._topic, event_type_name=event_type_name)

        return True


class SQSPublisher:
    def __init__(self, queue_name, dlq_name=None, driver=None, **kwargs):
        self._driver = driver or DriverManager.instance().get_driver()
        self._event_queue, self._dead_letter_queue = self._driver.declare_queue(
            queue_name,
            dead_letter_queue_name=dlq_name)
        self.default_message_group_id = kwargs.get('message_group_id')
        self.is_fifo = self._event_queue.attributes.get('FifoQueue') == 'true'

    def publish(self, event, event_type_name=None, **kwargs):
        if isinstance(event, dict) and 'event_type_name' in event:
            event_type_name = event['event_type_name']

        if not event_type_name:
            raise Exception('You need to supply the event_type_name either in the body of the event '
                            'or as parameter')

        if isinstance(event, dict):
            event['event_type_name'] = event_type_name

        content = EventSerializer.instance().serialize(event)

        message_group_id = kwargs.get('message_group_id', self.default_message_group_id)
        message_deduplication_id = (
            None if not self.is_fifo
            else kwargs.get('message_deduplication_id', str(uuid.uuid4()))
        )

        self._driver.queue_publish(
            content, self._event_queue, event_type_name=event_type_name,
            message_group_id=message_group_id,
            message_deduplication_id=message_deduplication_id
        )
