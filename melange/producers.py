import logging
import uuid
from typing import Any, List

from melange.backends.interfaces import AsyncMessagingBackend
from melange.models import Message, MessageDto
from melange.serializers.registry import SerializerRegistry

logger = logging.getLogger(__name__)


class AsyncQueuePublisher:
    def __init__(
        self,
        serializer_registry: SerializerRegistry,
        backend: AsyncMessagingBackend,
    ) -> None:
        self._backend = backend
        self._serializer_registry = serializer_registry

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
