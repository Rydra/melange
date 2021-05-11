import logging
import uuid

from melange.drivers.driver_manager import DriverManager
from melange.event_serializer import MessageSerializer

logger = logging.getLogger(__name__)


class ExchangeMessagePublisher:
    def __init__(self, message_serializer: MessageSerializer, topic, driver=None):
        self._driver = driver or DriverManager().get_driver()
        self.message_serializer = message_serializer
        self._topic_name = topic

    def init(self):
        self._topic = self._driver.declare_topic(self._topic_name)

    def publish(self, data, extra_attributes=None):
        content = self.message_serializer.serialize(data)
        manifest = self.message_serializer.manifest(data)

        self.init()
        self._driver.publish(
            content,
            self._topic,
            event_type_name=manifest,
            extra_attributes=extra_attributes,
        )

        return True


class SQSPublisher:
    def __init__(
        self,
        queue_name,
        message_serializer: MessageSerializer,
        dlq_name=None,
        driver=None,
        **kwargs
    ):
        self._driver = driver or DriverManager().get_driver()
        self.message_serializer = message_serializer
        self._event_queue, self._dead_letter_queue = self._driver.declare_queue(
            queue_name, dead_letter_queue_name=dlq_name
        )
        self.default_message_group_id = kwargs.get("message_group_id")
        self.is_fifo = self._event_queue.attributes.get("FifoQueue") == "true"

    def publish(self, data, **kwargs):
        content = self.message_serializer.serialize(data)
        manifest = self.message_serializer.manifest(data)

        message_group_id = kwargs.get("message_group_id", self.default_message_group_id)
        message_deduplication_id = (
            None
            if not self.is_fifo
            else kwargs.get("message_deduplication_id", str(uuid.uuid4()))
        )

        self._driver.queue_publish(
            content,
            self._event_queue,
            event_type_name=manifest,
            message_group_id=message_group_id,
            message_deduplication_id=message_deduplication_id,
        )
