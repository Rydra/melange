import logging
import uuid
from typing import Any, Optional

from melange.backends.backend_manager import BackendManager
from melange.backends.interfaces import Message, MessagingBackend
from melange.serializers.interfaces import MessageSerializer

logger = logging.getLogger(__name__)


class TopicPublisher:
    def __init__(
        self,
        message_serializer: MessageSerializer,
        backend: Optional[MessagingBackend] = None,
    ) -> None:
        self._backend = backend or BackendManager().get_default_backend()
        self.message_serializer = message_serializer

    def publish(self, topic_name: str, data: Any, **extra_attributes: Any) -> None:
        """
        Publishes data to a topic

        Args:
            topic_name: The topic to send the message to.
            data: The data to send to this topic. It will be serialized before sending to the
                topic using the serializers.
            **extra_attributes: Any extra attributes. They will be passed to the backend upon publishing.
        """
        topic = self._backend.declare_topic(topic_name)
        content = self.message_serializer.serialize(data)
        manifest = self.message_serializer.manifest(data)

        self._backend.publish_to_topic(
            Message.create(content, manifest),
            topic,
            extra_attributes=extra_attributes,
        )


class QueuePublisher:
    def __init__(
        self,
        message_serializer: MessageSerializer,
        backend: Optional[MessagingBackend] = None,
    ) -> None:
        self._backend = backend or BackendManager().get_default_backend()
        self.message_serializer = message_serializer

    def publish(self, queue_name: str, data: Any, **kwargs: Any) -> None:
        """
        Publishes data to a queue

        Args:
            queue_name: The queue to send the message to.
            data: The data to send to this queue. It will be serialized before sending to the
                queue using the serializers.
            **extra_attributes: Any extra attributes. They will be passed to the backend upon publish.
        """
        content = self.message_serializer.serialize(data)
        manifest = self.message_serializer.manifest(data)
        event_queue = self._backend.get_queue(queue_name)
        is_fifo = event_queue.unwrapped_obj.attributes.get("FifoQueue") == "true"
        default_message_group_id = kwargs.get("message_group_id")
        message_group_id = kwargs.get("message_group_id", default_message_group_id)

        message_deduplication_id = (
            None
            if not is_fifo
            else kwargs.get("message_deduplication_id", str(uuid.uuid4()))
        )

        self._backend.publish_to_queue(
            Message.create(content, manifest),
            event_queue,
            message_group_id=message_group_id,
            message_deduplication_id=message_deduplication_id,
        )
