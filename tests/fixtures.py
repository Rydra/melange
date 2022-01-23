import json
from typing import Any, Optional

from melange.consumers import SingleDispatchConsumer, consumer
from melange.serializers.interfaces import Serializer


class BaseMessage:
    pass


class MessageStubInterface(BaseMessage):
    pass


class BananaHappened(MessageStubInterface):
    def __init__(self, somevalue: Any) -> None:
        self.somevalue = somevalue


class NotBananaHappened(MessageStubInterface):
    pass


class ExceptionaleConsumer(SingleDispatchConsumer):
    @consumer
    def on_banana_event(self, event: BananaHappened) -> None:
        raise Exception("Sorry mate, I'm banana king")


class BananaConsumer(SingleDispatchConsumer):
    @consumer
    def on_banana_event(self, event: BananaHappened) -> None:
        pass


class NoBananaConsumer(SingleDispatchConsumer):
    @consumer
    def on_banana_event(self, event: NotBananaHappened) -> None:
        pass


class SerializerStub(Serializer):
    @staticmethod
    def identifier() -> int:
        return 40

    def manifest(self, data: Any) -> str:
        return "BananaEvent"

    def serialize(self, data: Any) -> str:
        if isinstance(data, BananaHappened):
            return json.dumps({"value": data.somevalue})
        return "apple"

    def deserialize(self, serialized_data: str, manifest: Optional[str] = None) -> Any:
        if serialized_data != "apple":
            data = json.loads(serialized_data)
            return BananaHappened(somevalue=data["value"])
