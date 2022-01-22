from typing import List, cast

from doubles import InstanceDouble, allow, expect

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
    backend = cast(
        MessagingBackend, InstanceDouble("melange.backends.interfaces.MessagingBackend")
    )
    allow(backend).get_queue.and_return({})
    allow(backend).retrieve_messages.and_return(messages)

    return backend


class TestMessageDispatcher:
    def test_consume_on_queue_with_messages(self):
        serializer = MessageSerializerStub()

        serialized_event = serializer.serialize(BananaHappened("apple"))
        messages = [Message.create(serialized_event) for _ in range(2)]
        backend = a_backend_with_messages(messages)

        consumer = BananaConsumer()
        expect(consumer).process.twice()
        expect(backend).acknowledge.twice()

        sut = SimpleMessageDispatcher(
            consumer, message_serializer=serializer, backend=backend
        )
        sut.consume_event("queue")

    def test_consume_on_queue_but_no_consumer_interested_in_the_messages(self):
        serializer = MessageSerializerStub()

        serialized_event = serializer.serialize(BananaHappened("apple"))
        messages = [Message.create(serialized_event) for _ in range(2)]
        backend = a_backend_with_messages(messages)

        consumer = NoBananaConsumer()
        expect(consumer).process.never()
        expect(backend).acknowledge.twice()

        sut = SimpleMessageDispatcher(
            consumer, message_serializer=serializer, backend=backend
        )
        sut.consume_event("queue")

    def test_if_a_consumer_raises_an_exception_the_message_is_not_acknowledged(self):
        serializer = MessageSerializerStub()

        serialized_event = serializer.serialize(BananaHappened("apple"))
        messages = [Message.create(serialized_event) for _ in range(2)]
        backend = a_backend_with_messages(messages)

        consumer = ExceptionaleConsumer()
        expect(backend).acknowledge.never()

        sut = SimpleMessageDispatcher(
            consumer, message_serializer=serializer, backend=backend
        )
        sut.consume_event("queue")
