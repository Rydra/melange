from simple_cqrs.domain_event import DomainEvent

from melange import QueuePublisher
from melange.backends import LocalSQSBackend
from melange.serializers import PickleSerializer, SerializerRegistry


class MyTestMessage:
    def __init__(self, message: str) -> None:
        self.message = message


if __name__ == "__main__":
    serializer_settings = {
        "serializers": {"pickle": PickleSerializer},
        "serializer_bindings": {DomainEvent: "pickle"},
    }

    serializer_registry = SerializerRegistry(serializer_settings)

    backend = LocalSQSBackend(host="localhost", port=9324)
    publisher = QueuePublisher(serializer_registry, backend)
    message = MyTestMessage("Hello World!")
    publisher.publish("melangetutorial-queue", message)
    print("Message sent successfully!")
