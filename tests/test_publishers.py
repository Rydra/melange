from typing import cast

from doublex import ANY_ARG, Spy, called
from hamcrest import *

from melange.backends.interfaces import MessagingBackend
from melange.publishers import QueuePublisher
from tests.fixtures import MessageSerializerStub


def a_backend() -> MessagingBackend:
    backend = Spy(MessagingBackend)

    with backend:
        backend.get_queue(ANY_ARG).returns({})

    return cast(MessagingBackend, backend)


class TestMessagePublisher:
    def test_publish_a_message_to_a_queue(self):
        backend = a_backend()
        serializer = MessageSerializerStub()

        sut = QueuePublisher(backend=backend, message_serializer=serializer)
        sut.publish("queue", {"some_content": "12345"})
        assert_that(backend.publish_to_queue, called().times(1))
