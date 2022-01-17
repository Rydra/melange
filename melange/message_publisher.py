import logging
import uuid
from typing import Any, Dict, Optional

from melange.backends.backend_manager import BackendManager
from melange.backends.interfaces import MessagingBackend
from melange.serializers.interfaces import MessageSerializer

logger = logging.getLogger(__name__)


class TopicPublisher:
    """
    Some documentation here is in order
    """

    def __init__(
        self,
        message_serializer: MessageSerializer,
        topic: str,
        backend: Optional[MessagingBackend] = None,
    ) -> None:
        self._backend = backend or BackendManager().get_backend()
        self.message_serializer = message_serializer
        self._topic_name = topic

    def init(self) -> None:
        self._topic = self._backend.declare_topic(self._topic_name)

    def publish(self, data: Any, extra_attributes: Optional[Dict] = None) -> bool:
        content = self.message_serializer.serialize(data)
        manifest = self.message_serializer.manifest(data)

        self.init()
        self._backend.publish(
            content,
            self._topic,
            event_type_name=manifest,
            extra_attributes=extra_attributes,
        )

        return True


class QueuePublisher:
    def __init__(
        self,
        message_serializer: MessageSerializer,
        backend: Optional[MessagingBackend] = None,
    ) -> None:
        self._backend = backend or BackendManager().get_backend()
        self.message_serializer = message_serializer

    def publish(self, queue_name: str, data: Any, **kwargs: Any) -> None:
        content = self.message_serializer.serialize(data)
        manifest = self.message_serializer.manifest(data)
        event_queue = self._backend.get_queue(queue_name)
        is_fifo = event_queue.attributes.get("FifoQueue") == "true"
        default_message_group_id = kwargs.get("message_group_id")
        message_group_id = kwargs.get("message_group_id", default_message_group_id)

        message_deduplication_id = (
            None
            if not is_fifo
            else kwargs.get("message_deduplication_id", str(uuid.uuid4()))
        )

        self._backend.queue_publish(
            content,
            event_queue,
            event_type_name=manifest,
            message_group_id=message_group_id,
            message_deduplication_id=message_deduplication_id,
        )
