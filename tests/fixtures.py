import json
from typing import Any, Dict, Optional

from melange import SingleDispatchConsumer, consumer
from melange.consumers import AsyncConsumer, AsyncSingleDispatchConsumer, async_consumer
from melange.serializers import Serializer


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


class AsyncExceptionaleConsumer(AsyncSingleDispatchConsumer):
    @async_consumer
    async def on_banana_event(self, event: BananaHappened) -> None:
        raise Exception("Sorry mate, I'm banana king")


class BananaConsumer(SingleDispatchConsumer):
    @consumer
    def on_banana_event(self, event: BananaHappened) -> None:
        pass


class AsyncBananaConsumer(AsyncConsumer):
    pass


class NoBananaConsumer(SingleDispatchConsumer):
    @consumer
    def on_banana_event(self, event: NotBananaHappened) -> None:
        pass


class AsyncNoBananaConsumer(AsyncSingleDispatchConsumer):
    def __init__(self, call_registry: Dict) -> None:
        self.call_registry = call_registry

    @async_consumer
    async def on_banana_event(self, event: NotBananaHappened) -> None:
        self.call_registry["banana_event"] = 1


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
