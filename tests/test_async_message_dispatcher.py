from collections import defaultdict
from typing import AsyncIterable, Dict, List

from hamcrest import *

from melange.backends.interfaces import AsyncMessagingBackend
from melange.message_dispatcher import AsyncSimpleMessageDispatcher
from melange.models import Message
from melange.serializers import JsonSerializer, PickleSerializer, SerializerRegistry
from tests.fixtures import (
    AsyncBananaConsumer,
    AsyncExceptionaleConsumer,
    AsyncNoBananaConsumer,
    BananaHappened,
    BaseMessage,
    MessageStubInterface,
    SerializerStub,
)


async def wrap_async(obj):
    return obj


async def wrap_async_iterable(obj):
    for i in obj:
        yield i


class StubAsyncMessagingBackend(AsyncMessagingBackend):
    def __init__(self, messages: List[Message], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.messages = messages
        self.call_count = defaultdict(lambda: 0)

    async def get_queue(self, queue_name: str):
        return {}

    async def retrieve_messages(self, queue, **kwargs) -> AsyncIterable[Message]:
        for message in self.messages:
            yield message

    async def yield_messages(self, queue, **kwargs) -> AsyncIterable[Message]:
        for message in self.messages:
            yield message

    async def acknowledge(self, message: Message) -> None:
        self.call_count["acknowledge"] += 1
        return None


def a_backend_with_messages(messages: List[Message]) -> AsyncMessagingBackend:
    return StubAsyncMessagingBackend(messages)


serializer_settings = {
    "serializers": {
        "json": JsonSerializer,
        "pickle": PickleSerializer,
        "test": SerializerStub,
    },
    "serializer_bindings": {
        Dict: "json",
        MessageStubInterface: "test",
        BaseMessage: "test",
    },
    "default": "pickle",
}


class TestAsyncMessageDispatcher:
    async def test_consume_on_queue_with_messages(self, anyio_backend):
        serializer = SerializerStub()

        serialized_event = serializer.serialize(BananaHappened("apple"))
        messages = [
            Message.create(serialized_event, None, serializer.identifier())
            for _ in range(2)
        ]
        backend = a_backend_with_messages(messages)

        num_calls = 0

        async def _(message):
            nonlocal num_calls
            num_calls += 1

        consumer = AsyncBananaConsumer(_)

        registry = SerializerRegistry(serializer_settings)
        sut = AsyncSimpleMessageDispatcher(
            consumer, serializer_registry=registry, backend=backend
        )
        await sut.consume_event("queue", preserve_order=True)

        assert_that(num_calls, is_(2))

    async def test_consume_on_queue_but_no_consumer_interested_in_the_messages(
        self, anyio_backend
    ):
        serializer = SerializerStub()

        serialized_event = serializer.serialize(BananaHappened("apple"))
        messages = [
            Message.create(serialized_event, None, serializer.identifier())
            for _ in range(2)
        ]
        backend = a_backend_with_messages(messages)

        call_registry = {}
        consumer = AsyncNoBananaConsumer(call_registry)

        registry = SerializerRegistry(serializer_settings)
        sut = AsyncSimpleMessageDispatcher(
            consumer, serializer_registry=registry, backend=backend
        )
        await sut.consume_event("queue")

        assert_that(call_registry, not_(has_key("banana")))
        assert_that(backend.call_count["acknowledge"], is_(2))

    async def test_if_a_consumer_raises_an_exception_the_message_is_not_acknowledged(
        self, anyio_backend
    ):
        serializer = SerializerStub()

        serialized_event = serializer.serialize(BananaHappened("apple"))
        messages = [
            Message.create(serialized_event, None, serializer.identifier())
            for _ in range(2)
        ]
        backend = a_backend_with_messages(messages)

        consumer = AsyncExceptionaleConsumer()

        registry = SerializerRegistry(serializer_settings)
        sut = AsyncSimpleMessageDispatcher(
            consumer, serializer_registry=registry, backend=backend
        )
        await sut.consume_event("queue")
        assert_that(backend.call_count["acknowledge"], is_(0))
