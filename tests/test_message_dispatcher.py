from typing import List, cast

from doublex import ANY_ARG, ProxySpy, Spy, called, never
from hamcrest import *

from melange.backends.interfaces import MessagingBackend
from melange.message_dispatcher import SimpleMessageDispatcher
from melange.models import Message
from tests.fixtures import (
    BananaConsumer,
    BananaHappened,
    ExceptionaleConsumer,
    MessageSerializerStub,
    NoBananaConsumer,
)


def a_backend_with_messages(messages: List[Message]) -> MessagingBackend:
    backend = Spy(MessagingBackend)

    with backend:
        backend.get_queue(ANY_ARG).returns({})
        backend.retrieve_messages(ANY_ARG).returns(messages)

    return cast(MessagingBackend, backend)


class TestMessageDispatcher:
    def test_consume_on_queue_with_messages(self):
        serializer = MessageSerializerStub()

        serialized_event = serializer.serialize(BananaHappened("apple"))
        messages = [Message.create(serialized_event) for _ in range(2)]
        backend = a_backend_with_messages(messages)

        consumer = ProxySpy(BananaConsumer())

        sut = SimpleMessageDispatcher(
            consumer, message_serializer=serializer, backend=backend
        )
        sut.consume_event("queue")

        assert_that(consumer.process, called().times(2))
        assert_that(backend.acknowledge, called().times(2))

    def test_consume_on_queue_but_no_consumer_interested_in_the_messages(self):
        serializer = MessageSerializerStub()

        serialized_event = serializer.serialize(BananaHappened("apple"))
        messages = [Message.create(serialized_event) for _ in range(2)]
        backend = a_backend_with_messages(messages)

        consumer = ProxySpy(NoBananaConsumer())

        sut = SimpleMessageDispatcher(
            consumer, message_serializer=serializer, backend=backend
        )
        sut.consume_event("queue")

        assert_that(consumer.process, never(called()))
        assert_that(backend.acknowledge, called().times(2))

    def test_if_a_consumer_raises_an_exception_the_message_is_not_acknowledged(self):
        serializer = MessageSerializerStub()

        serialized_event = serializer.serialize(BananaHappened("apple"))
        messages = [Message.create(serialized_event) for _ in range(2)]
        backend = a_backend_with_messages(messages)

        consumer = ExceptionaleConsumer()

        sut = SimpleMessageDispatcher(
            consumer, message_serializer=serializer, backend=backend
        )
        sut.consume_event("queue")
        assert_that(backend.acknowledge, never(called()))
