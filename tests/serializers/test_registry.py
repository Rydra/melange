from typing import Dict

from hamcrest import *

from melange.serializers.json import JsonSerializer
from melange.serializers.pickle import PickleSerializer
from melange.serializers.registry import SerializerRegistry, sort
from tests.fixtures import (
    BananaHappened,
    BaseMessage,
    MessageSerializerStub,
    MessageStubInterface,
)


class TestSerializerRegistry:
    def test_sort(self):
        list_serializers = [
            (BaseMessage, MessageSerializerStub),
            (MessageStubInterface, MessageSerializerStub),
        ]

        result = sort(list_serializers)
        assert_that(result, is_([list_serializers[1], list_serializers[0]]))

    def test_a(self):
        test_settings = {
            "serializers": {
                "json": JsonSerializer,
                "pickle": PickleSerializer,
                "test": MessageSerializerStub,
            },
            "serializer_bindings": {
                Dict: "json",
                MessageStubInterface: "test",
                BaseMessage: "test",
            },
            "default": "pickle",
        }

        serializer_reg = SerializerRegistry(test_settings)

        message_serializer = serializer_reg.find_serializer_for(BananaHappened(1))
        assert_that(message_serializer, is_(MessageSerializerStub))
