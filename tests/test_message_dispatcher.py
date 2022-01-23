from typing import Dict, List, cast

from doublex import ANY_ARG, ProxySpy, Spy, called, never
from hamcrest import *

from melange.backends.interfaces import MessagingBackend
from melange.message_dispatcher import SimpleMessageDispatcher
from melange.models import Message
from melange.serializers.json import JsonSerializer
from melange.serializers.pickle import PickleSerializer
from melange.serializers.registry import SerializerRegistry
from tests.fixtures import (
    BananaConsumer,
    BananaHappened,
    BaseMessage,
    ExceptionaleConsumer,
    MessageStubInterface,
    NoBananaConsumer,
    SerializerStub,
)


def a_backend_with_messages(messages: List[Message]) -> MessagingBackend:
    backend = Spy(MessagingBackend)

    with backend:
        backend.get_queue(ANY_ARG).returns({})
        backend.retrieve_messages(ANY_ARG).returns(messages)
        backend.yield_messages(ANY_ARG).returns(messages)

    return cast(MessagingBackend, backend)


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


class TestMessageDispatcher:
    def test_consume_on_queue_with_messages(self):
        serializer = SerializerStub()

        serialized_event = serializer.serialize(BananaHappened("apple"))
        messages = [
            Message.create(serialized_event, None, serializer.identifier())
            for _ in range(2)
        ]
        backend = a_backend_with_messages(messages)

        consumer = ProxySpy(BananaConsumer())

        registry = SerializerRegistry(serializer_settings)
        sut = SimpleMessageDispatcher(
            consumer, serializer_registry=registry, backend=backend
        )
        sut.consume_event("queue")

        assert_that(consumer.process, called().times(2))
        assert_that(backend.acknowledge, called().times(2))

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
