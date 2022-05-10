import logging
import uuid
from typing import Any, List, Optional

from melange.backends.backend_manager import BackendManager
from melange.backends.interfaces import AsyncMessagingBackend, MessagingBackend
from melange.models import Message, MessageDto
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


class AsyncQueuePublisher:
    def __init__(
        self,
        serializer_registry: SerializerRegistry,
        backend: AsyncMessagingBackend,
    ) -> None:
        self._backend = backend
        self._serializer_registry = serializer_registry

    async def publish(self, queue_name: str, data: Any, **kwargs: Any) -> None:
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
        queue = await self._backend.get_queue(queue_name)

        await self._backend.publish_to_queue(
            Message.create(content, manifest, serializer.identifier()), queue, **kwargs
        )

    async def publish_batch(self, queue_name: str, data: List[Any]) -> None:
        message_dtos: List[MessageDto] = []
        queue = await self._backend.get_queue(queue_name)
        attributes = await self._backend.get_queue_attributes(queue)
        is_fifo = attributes.get("FifoQueue") == "true"

        for entry in data:
            serializer = self._serializer_registry.find_serializer_for(entry)
            content = serializer.serialize(entry["object"])
            manifest = serializer.manifest(entry["object"])

            message_group_id = entry.get("message_group_id", str(uuid.uuid4()))
            message_deduplication_id = (
                None
                if not is_fifo
                else entry.get("message_deduplication_id", str(uuid.uuid4()))
            )

            message_dtos.append(
                MessageDto(
                    Message.create(content, manifest, serializer.identifier()),
                    message_group_id,
                    message_deduplication_id,
                )
            )

        await self._backend.publish_to_queue_batch(message_dtos, queue)
