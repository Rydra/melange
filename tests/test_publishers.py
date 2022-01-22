from typing import cast

from bunch import Bunch
from doubles import InstanceDouble, allow, expect

from melange.backends.interfaces import MessagingBackend
from melange.publishers import QueuePublisher
from tests.fixtures import MessageSerializerStub


def a_backend() -> MessagingBackend:
    backend = cast(
        MessagingBackend, InstanceDouble("melange.backends.interfaces.MessagingBackend")
    )
    allow(backend).get_queue.and_return(Bunch(attributes={"FifoQueue": "true"}))

    return backend


class TestMessagePublisher:
    def test_publish_a_message_to_a_queue(self):
        backend = a_backend()
        serializer = MessageSerializerStub()
        expect(backend).publish_to_queue.once()

        sut = QueuePublisher(backend=backend, message_serializer=serializer)
        sut.publish("queue", {"some_content": "12345"})
