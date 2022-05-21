import uuid
from dataclasses import dataclass
from types import TracebackType
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Type

from melange.backends.sqs.sqs_backend_async import AsyncBaseSQSBackend
from melange.models import Message, MessageDto, QueueWrapper
from melange.serializers import JsonSerializer


@dataclass
class ValueContainer:
    value: Any
    message_group_id: Optional[str] = None
    message_deduplication_id: Optional[str] = None


class AIOSQSProducer:
    def __init__(
        self,
        queue_name: str,
        key_serializer: Optional[Callable[[Any], str]] = None,
        value_serializer: Optional[Callable[[Any], str]] = None,
        max_number_of_messages: int = 10,
        visibility_timeout: int = 100,
        wait_time_seconds: int = 10,
        **kwargs: Any,
    ) -> None:
        self._backend = AsyncBaseSQSBackend(
            max_number_of_messages=max_number_of_messages,
            visibility_timeout=visibility_timeout,
            wait_time_seconds=wait_time_seconds,
            extra_settings=kwargs,
        )
        self.key_serializer = key_serializer
        self.value_serializer = value_serializer or JsonSerializer().serialize
        self.queue_name = queue_name
        self.queue: Optional[QueueWrapper] = None
        self.queue_attributes: Optional[Dict] = None

    async def start(self) -> None:
        self.queue = await self._backend.get_queue(self.queue_name)
        self.queue_attributes = await self._backend.get_queue_attributes(self.queue)

    async def send(self, value: Any, **kwargs: Any) -> None:
        """
        Publishes data to a queue

        Args:
            data: The data to send to this queue. It will be serialized before sending to the
                queue using the serializers.
            **kwargs: Any extra attributes. They will be passed to the backend upon publish.
        """
        if not self.queue:
            raise Exception(
                "Initialize first the queue by calling the start() method "
                "of the consumer or using a context manager"
            )

        content = self.value_serializer(value)

        await self._backend.publish_to_queue(
            Message.create(content, None, 0), self.queue, **kwargs
        )

    async def send_batch(self, entries: List[ValueContainer]) -> None:
        """
        Publishes data to a queue

        Args:
            entries: The data to send to this queue. It will be serialized before sending to the
                queue using the serializers.
            **kwargs: Any extra attributes. They will be passed to the backend upon publish.
        """
        if not self.queue:
            raise Exception(
                "Initialize first the queue by calling the start() method "
                "of the consumer or using a context manager"
            )

        message_dtos: List[MessageDto] = []

        assert self.queue_attributes
        is_fifo = self.queue_attributes.get("FifoQueue") == "true"

        for entry in entries:
            content = self.value_serializer(entry.value)

            message_group_id = entry.message_group_id or str(uuid.uuid4())
            message_deduplication_id = (
                None
                if not is_fifo
                else (entry.message_deduplication_id or str(uuid.uuid4()))
            )

            message_dtos.append(
                MessageDto(
                    Message.create(content, None, 0),
                    message_group_id,
                    message_deduplication_id,
                )
            )

        await self._backend.publish_to_queue_batch(message_dtos, self.queue)

    async def __aenter__(self) -> "AIOSQSProducer":
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.queue = None
        self.queue_attributes = None


class AIOSQSConsumer:
    def __init__(
        self,
        queue_name: str,
        key_deserializer: Optional[Callable[[str], Any]] = None,
        value_deserializer: Optional[Callable[[str], Any]] = None,
        max_number_of_messages: int = 10,
        visibility_timeout: int = 100,
        wait_time_seconds: int = 10,
        enable_auto_commit: bool = True,
        **kwargs: Any,
    ) -> None:
        self._backend = AsyncBaseSQSBackend(
            max_number_of_messages=max_number_of_messages,
            visibility_timeout=visibility_timeout,
            wait_time_seconds=wait_time_seconds,
            extra_settings=kwargs,
        )
        self.queue_name = queue_name
        self.key_deserializer = key_deserializer
        self.value_deserializer = value_deserializer or JsonSerializer().deserialize
        self.queue: Optional[QueueWrapper] = None
        self.enable_auto_commit = enable_auto_commit
        self.uncommitted_messages: List[Message] = []

    async def start(self) -> None:
        self.queue = await self._backend.get_queue(self.queue_name)

    async def __aenter__(self) -> "AIOSQSConsumer":
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.queue = None

    async def commit(self, message: Optional[Message] = None) -> None:
        if message:
            self.uncommitted_messages.remove(message)
            await self._backend.acknowledge(message)
        else:
            messages = self.uncommitted_messages.copy()
            self.uncommitted_messages.clear()
            await self._backend.acknowledge_batch(messages)

    async def consume(self) -> AsyncIterator[Any]:
        if not self.queue:
            raise Exception(
                "Initialize first the queue by calling the start() method "
                "of the consumer or using a context manager"
            )
        while True:
            async for message in self._backend.retrieve_messages(self.queue):
                if self.enable_auto_commit:
                    await self._backend.acknowledge(message)
                else:
                    self.uncommitted_messages.append(message)

                value = self.value_deserializer(message.content)
                yield value

    def __aiter__(self) -> AsyncIterator[Any]:
        return self.consume()
