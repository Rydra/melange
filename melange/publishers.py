import logging
from typing import Any, Optional

from melange.backends.backend_manager import BackendManager
from melange.backends.interfaces import MessagingBackend
from melange.models import Message
from melange.serializers.registry import SerializerRegistry

logger = logging.getLogger(__name__)


class TopicPublisher:
    def __init__(
        self,
        serializer_registry: SerializerRegistry,
        backend: Optional[MessagingBackend] = None,
    ) -> None:
        self._backend = backend or BackendManager().get_default_backend()
        self._serializer_registry = serializer_registry

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
        serializer = self._serializer_registry.find_serializer_for(data)
        content = serializer.serialize(data)
        manifest = serializer.manifest(data)

        self._backend.publish_to_topic(
            Message.create(content, manifest, serializer.identifier()),
            topic,
            extra_attributes=extra_attributes,
        )


class QueuePublisher:
    def __init__(
        self,
        serializer_registry: SerializerRegistry,
        backend: Optional[MessagingBackend] = None,
    ) -> None:
        self._backend = backend or BackendManager().get_default_backend()
        self._serializer_registry = serializer_registry

    def publish(self, queue_name: str, data: Any, **kwargs: Any) -> None:
        """
        Publishes data to a queue

        Args:
            queue_name: The queue to send the message to.
            data: The data to send to this queue. It will be serialized before sending to the
                queue using the serializers.
            **kwargs: Any extra attributes. They will be passed to the backend upon publish.
        """
        serializer = self._serializer_registry.find_serializer_for(data)
        content = serializer.serialize(data)
        manifest = serializer.manifest(data)
        queue = self._backend.get_queue(queue_name)

        self._backend.publish_to_queue(
            Message.create(content, manifest, serializer.identifier()), queue, **kwargs
        )
