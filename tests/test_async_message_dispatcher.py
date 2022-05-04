from typing import AsyncIterable, Dict, List

from doublex import ProxySpy, called, never
from hamcrest import *

from melange import SimpleMessageDispatcher
from melange.backends.interfaces import AsyncMessagingBackend
from melange.message_dispatcher import AsyncSimpleMessageDispatcher
from melange.models import Message
from melange.serializers import JsonSerializer, PickleSerializer, SerializerRegistry
from tests.fixtures import (
    AsyncBananaConsumer,
    BananaHappened,
    BaseMessage,
    ExceptionaleConsumer,
    MessageStubInterface,
    NoBananaConsumer,
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

    async def get_queue(self, queue_name: str):
        return {}

    async def retrieve_messages(self, queue, **kwargs) -> AsyncIterable[Message]:
        for message in self.messages:
            yield message

    async def yield_messages(self, queue, **kwargs) -> AsyncIterable[Message]:
        for message in self.messages:
            yield message

    async def acknowledge(self, message: Message) -> None:
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

    def test_consume_on_queue_but_no_consumer_interested_in_the_messages(self):
        serializer = SerializerStub()

        serialized_event = serializer.serialize(BananaHappened("apple"))
        messages = [
            Message.create(serialized_event, None, serializer.identifier())
            for _ in range(2)
        ]
        backend = a_backend_with_messages(messages)

        consumer = ProxySpy(NoBananaConsumer())

        registry = SerializerRegistry(serializer_settings)
        sut = SimpleMessageDispatcher(
            consumer, serializer_registry=registry, backend=backend
        )
        sut.consume_event("queue")

        assert_that(consumer.process, never(called()))
        assert_that(backend.acknowledge, called().times(2))

    def test_if_a_consumer_raises_an_exception_the_message_is_not_acknowledged(self):
        serializer = SerializerStub()

        serialized_event = serializer.serialize(BananaHappened("apple"))
        messages = [
            Message.create(serialized_event, None, serializer.identifier())
            for _ in range(2)
        ]
        backend = a_backend_with_messages(messages)

        consumer = ExceptionaleConsumer()

        registry = SerializerRegistry(serializer_settings)
        sut = SimpleMessageDispatcher(
            consumer, serializer_registry=registry, backend=backend
        )
        sut.consume_event("queue")
        assert_that(backend.acknowledge, never(called()))
