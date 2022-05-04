import asyncio
import logging
from typing import Any, Callable, List, Optional, Union

from anyio import (
    CancelScope,
    CapacityLimiter,
    create_memory_object_stream,
    create_task_group,
)
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream

from melange.backends.backend_manager import BackendManager
from melange.backends.interfaces import AsyncMessagingBackend, MessagingBackend
from melange.consumers import AsyncConsumer, Consumer
from melange.exceptions import SerializationError
from melange.infrastructure.cache import DeduplicationCache, NullCache
from melange.models import Message, QueueWrapper
from melange.serializers.registry import SerializerRegistry
from melange.utils import get_fully_qualified_name

# TODO: Clear code duplication between the dispatcher and the handler. Fix.

logger = logging.getLogger(__name__)


class MessageDispatcher:
    """
    The `MessageDispatcher` is responsible to start the message consumption loop
    to retrieve the available messages from the queue and dispatch them to the
    consumers.
    """

    def __init__(
        self,
        serializer_registry: SerializerRegistry,
        cache: Optional[DeduplicationCache] = None,
        backend: Optional[MessagingBackend] = None,
        always_ack: bool = False,
        early_ack: bool = False,
    ) -> None:
        """

        Args:
            serializer_registry:
            cache:
            backend:
            always_ack:
            early_ack: Whether the incoming message should be acknowledged immediately
            upon receiving. Overrides `always_ack`. Useful when the message
            processing is long and you need to skip the visibility timeout of SQS
        """
        self._consumers: List[Consumer] = []
        self.serializer_registry = serializer_registry
        self._backend = backend or BackendManager().get_default_backend()
        self.cache: DeduplicationCache = cache or NullCache()
        self.always_ack = always_ack
        self.early_ack = early_ack

    def attach_consumer(self, consumer: Consumer) -> None:
        """
        Attaches a consumer to the dispatcher, so that it can receive messages
        Args:
            consumer: the consumer to attach
        """
        if consumer not in self._consumers:
            self._consumers.append(consumer)

    def unattach_consumer(self, consumer: Consumer) -> None:
        """
        Unattaches the consumer from the dispatcher, so that it will not receive messages anymore
        Args:
            consumer: the consumer to unattach
        """
        if consumer in self._consumers:
            self._consumers.remove(consumer)

    def consume_loop(
        self,
        queue_name: str,
        on_exception: Optional[Callable[[Exception], None]] = None,
        after_consume: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        Starts the consumption loop on the queue `queue_name`
        Args:
            queue_name: The queue to poll for new messages
            on_exception: If there is any exception, the exception
                will be passed to this callback
            after_consume: After consuming a batch of events,
                invoke this callback
        """
        self.consume_event(queue_name, on_exception, after_consume)

    def consume_event(
        self,
        queue_name: str,
        on_exception: Optional[Callable[[Exception], None]] = None,
        after_consume: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        Consumes events on the queue `queue_name`
        """
        event_queue = self._backend.get_queue(queue_name)

        messages = self._backend.yield_messages(event_queue)
        for message in messages:
            try:
                if self.early_ack:
                    self._backend.acknowledge(message)

                self._dispatch_message(message)
            except Exception as e:
                logger.exception(e)
                if on_exception:
                    on_exception(e)
            finally:
                if after_consume:
                    after_consume()

    def _get_consumers(self, message_data: Any) -> List[Consumer]:
        return [
            consumer for consumer in self._consumers if consumer.accepts(message_data)
        ]

    def _dispatch_message(self, message: Message) -> None:
        manifest = message.get_message_manifest()

        # If the message cannot be deserialized, just ignore it.
        # ACK it anyway to avoid hanging on the same message over an over again
        try:
            if message.serializer_id is not None:
                message_data = self.serializer_registry.deserialize_with_serializerid(
                    message.content, message.serializer_id, manifest=manifest
                )
            else:
                # TODO: If no serializerid is supplied, at least we need to grab some
                # clue in the message to know which serializer must be used.
                # for now, rely on the default.
                message_data = self.serializer_registry.deserialize_with_class(
                    message.content, object, manifest=manifest
                )
        except SerializationError as e:
            logger.error(e)
            self._backend.acknowledge(message)
            return

        consumers = self._get_consumers(message_data)

        successful = 0
        for consumer in consumers:
            try:
                # Store into the cache
                message_key = (
                    f"{get_fully_qualified_name(consumer)}.{message.message_id}"
                )

                if message_key in self.cache:
                    logger.info("detected a duplicated message, ignoring")
                else:
                    consumer.process(message_data, message_id=message.message_id)
                    successful += 1
                    self.cache.store(message_key, message_key)
            except Exception as e:
                logger.exception(e)

        if not self.early_ack and (self.always_ack or successful == len(consumers)):
            self._backend.acknowledge(message)


class AsyncMessageDispatcher:
    """
    The `MessageDispatcher` is responsible to start the message consumption loop
    to retrieve the available messages from the queue and dispatch them to the
    consumers.
    """

    def __init__(
        self,
        serializer_registry: SerializerRegistry,
        backend: AsyncMessagingBackend,
        cache: Optional[DeduplicationCache] = None,
        always_ack: bool = False,
        early_ack: bool = False,
    ) -> None:
        """

        Args:
            serializer_registry:
            cache:
            backend:
            always_ack:
            early_ack: Whether the incoming message should be acknowledged immediately
            upon receiving. Overrides `always_ack`. Useful when the message
            processing is long and you need to skip the visibility timeout of SQS
        """
        self._consumers: List[Consumer] = []
        self.serializer_registry = serializer_registry
        self._backend = backend
        self.cache: DeduplicationCache = cache or NullCache()
        self.always_ack = always_ack
        self.early_ack = early_ack

    def attach_consumer(self, consumer: Consumer) -> None:
        """
        Attaches a consumer to the dispatcher, so that it can receive messages
        Args:
            consumer: the consumer to attach
        """
        if consumer not in self._consumers:
            self._consumers.append(consumer)

    def unattach_consumer(self, consumer: Consumer) -> None:
        """
        Unattaches the consumer from the dispatcher, so that it will not receive messages anymore
        Args:
            consumer: the consumer to unattach
        """
        if consumer in self._consumers:
            self._consumers.remove(consumer)

    async def consume_event(
        self,
        queue_name: str,
        message_processing_limit: Optional[CapacityLimiter] = None,
        preserve_order: bool = False,
        on_exception: Optional[Callable[[Exception], None]] = None,
        after_consume: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        Starts the consumption loop on the queue `queue_name`
        Args:
            queue_name: The queue to poll for new messages
            on_exception: If there is any exception, the exception
                will be passed to this callback
            after_consume: After consuming a batch of events,
                invoke this callback
        """
        queue = await self._backend.get_queue(queue_name)

        send_stream, receive_stream = create_memory_object_stream(max_buffer_size=20)
        message_processing_limit = message_processing_limit or CapacityLimiter(1)
        async with create_task_group() as tg:
            tg.start_soon(self.receive_and_conume, send_stream, queue)
            if preserve_order:
                tg.start_soon(
                    self.start_ordered_message_consumer,
                    receive_stream,
                    message_processing_limit,
                    after_consume,
                )
            else:
                tg.start_soon(
                    self.start_unordered_message_consumer,
                    receive_stream,
                    message_processing_limit,
                    after_consume,
                )

    async def consume_loop(
        self,
        queue_name: str,
        message_processing_limit: Optional[CapacityLimiter] = None,
        preserve_order: bool = False,
        on_exception: Optional[Callable[[Exception], None]] = None,
        after_consume: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        Consumes events on the queue `queue_name`
        """
        queue = await self._backend.get_queue(queue_name)

        send_stream, receive_stream = create_memory_object_stream(max_buffer_size=20)
        message_processing_limit = message_processing_limit or CapacityLimiter(1)
        async with create_task_group() as tg:
            tg.start_soon(self.start_message_producer, send_stream, queue)
            if preserve_order:
                tg.start_soon(
                    self.start_ordered_message_consumer,
                    receive_stream,
                    message_processing_limit,
                    after_consume,
                )
            else:
                tg.start_soon(
                    self.start_unordered_message_consumer,
                    receive_stream,
                    message_processing_limit,
                    after_consume,
                )

    async def receive_and_conume(
        self, send_stream: MemoryObjectSendStream, queue: QueueWrapper
    ) -> None:
        async with send_stream:
            messages = self._backend.retrieve_messages(queue)
            async for message in messages:
                if self.early_ack:
                    await self._backend.acknowledge(message)
                await send_stream.send(message)

    async def start_message_producer(
        self, send_stream: MemoryObjectSendStream, queue: QueueWrapper
    ) -> None:
        async with send_stream:
            while True:
                messages = self._backend.retrieve_messages(queue)
                async for message in messages:
                    if self.early_ack:
                        await self._backend.acknowledge(message)
                    await send_stream.send(message)

    async def wrap(
        self, after_consume: Optional[Callable[[], None]], f: Callable, *args: Any
    ) -> None:
        try:
            await f(*args)
        finally:
            if after_consume:
                after_consume()

    async def start_unordered_message_consumer(
        self,
        receive_stream: MemoryObjectReceiveStream,
        message_processing_limit: CapacityLimiter,
        after_consume: Optional[Callable[[], None]] = None,
    ) -> None:
        async with create_task_group() as tg, receive_stream:
            with CancelScope(shield=True):
                async for message in receive_stream:
                    tg.start_soon(
                        self.wrap,
                        after_consume,
                        self._dispatch_message,
                        message_processing_limit,
                        message,
                    )

    async def start_ordered_message_consumer(
        self,
        receive_stream: MemoryObjectReceiveStream,
        message_processing_limit: CapacityLimiter,
        after_consume: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        Processes events waiting for the full processing of one event before proceeding to the next
        """
        async with receive_stream:
            async for message in receive_stream:
                try:
                    await self._dispatch_message(message_processing_limit, message)
                finally:
                    if after_consume:
                        after_consume()

    def _get_consumers(self, message_data: Any) -> List[Union[Consumer, AsyncConsumer]]:
        return [
            consumer for consumer in self._consumers if consumer.accepts(message_data)
        ]

    async def _dispatch_message(
        self, limiter: CapacityLimiter, message: Message
    ) -> None:
        async with limiter:
            manifest = message.get_message_manifest()

            # If the message cannot be deserialized, just ignore it.
            # ACK it anyway to avoid hanging on the same message over an over again
            try:
                if message.serializer_id is not None:
                    message_data = (
                        self.serializer_registry.deserialize_with_serializerid(
                            message.content, message.serializer_id, manifest=manifest
                        )
                    )
                else:
                    # TODO: If no serializerid is supplied, at least we need to grab some
                    # clue in the message to know which serializer must be used.
                    # for now, rely on the default.
                    message_data = self.serializer_registry.deserialize_with_class(
                        message.content, object, manifest=manifest
                    )
            except SerializationError as e:
                logger.error(e)
                if not self.early_ack:
                    # If not early ack, it means that the message has not been
                    # acked yet
                    await self._backend.acknowledge(message)
                return

            consumers = self._get_consumers(message_data)

            successful = 0
            for consumer in consumers:
                try:
                    # Store into the cache
                    message_key = (
                        f"{get_fully_qualified_name(consumer)}.{message.message_id}"
                    )

                    if message_key in self.cache:
                        logger.info("detected a duplicated message, ignoring")
                    else:
                        if isinstance(
                            consumer, AsyncConsumer
                        ) and asyncio.iscoroutinefunction(consumer.process):
                            await consumer.process(
                                message_data, message_id=message.message_id
                            )
                        else:
                            consumer.process(
                                message_data, message_id=message.message_id
                            )
                        successful += 1
                        self.cache.store(message_key, message_key)
                except Exception as e:
                    logger.exception(e)

            if not self.early_ack and (self.always_ack or successful == len(consumers)):
                await self._backend.acknowledge(message)


class SimpleMessageDispatcher(MessageDispatcher):
    """
    Handles the retrieval of messages from a queue and
    dispatches the messages to a single consumer. A simpler version
    of the `MessageDispatcher`
    """

    def __init__(
        self,
        consumer: Consumer,
        serializer_registry: SerializerRegistry,
        cache: Optional[DeduplicationCache] = None,
        backend: Optional[MessagingBackend] = None,
        always_ack: bool = False,
        early_ack: bool = False,
    ):
        super().__init__(serializer_registry, cache, backend, always_ack, early_ack)
        self.attach_consumer(consumer)


class AsyncSimpleMessageDispatcher(AsyncMessageDispatcher):
    """
    Handles the retrieval of messages from a queue and
    dispatches the messages to a single consumer. A simpler version
    of the `MessageDispatcher`
    """

    def __init__(
        self,
        consumer: Consumer,
        serializer_registry: SerializerRegistry,
        backend: AsyncMessagingBackend,
        cache: Optional[DeduplicationCache] = None,
        always_ack: bool = False,
        early_ack: bool = False,
    ):
        super().__init__(serializer_registry, backend, cache, always_ack, early_ack)
        self.attach_consumer(consumer)
