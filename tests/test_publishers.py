from typing import Dict, cast

from doublex import ANY_ARG, Spy, called
from hamcrest import *

from melange.backends.interfaces import MessagingBackend
from melange.publishers import QueuePublisher
from melange.serializers.json import JsonSerializer
from melange.serializers.pickle import PickleSerializer
from melange.serializers.registry import SerializerRegistry
from tests.fixtures import BaseMessage, MessageStubInterface, SerializerStub


def a_backend() -> MessagingBackend:
    backend = Spy(MessagingBackend)

    with backend:
        backend.get_queue(ANY_ARG).returns({})

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


class TestMessagePublisher:
    def test_publish_a_message_to_a_queue(self):
        backend = a_backend()

        registry = SerializerRegistry(serializer_settings)
        sut = QueuePublisher(backend=backend, serializer_registry=registry)
        sut.publish("queue", {"some_content": "12345"})
        assert_that(backend.publish_to_queue, called().times(1))
