from melange import Consumer, QueuePublisher
from melange.backends import InMemoryMessagingBackend, link_synchronously
from melange.serializers import PickleSerializer, SerializerRegistry

serializer_settings = {
    "serializers": {
        "pickle": PickleSerializer,
    },
    "serializer_bindings": {},
    "default": "pickle",
}


def test_inmemory_messaging_backend():
    consumer_1 = Consumer(lambda message: print(f"Hello {message['message']}!"))
    consumer_2 = Consumer(lambda message: print(f"Hello {message['message']} 2!"))

    backend = InMemoryMessagingBackend()
    registry = SerializerRegistry(serializer_settings)
    link_synchronously("somequeue", [consumer_1, consumer_2], registry, backend)

    registry = SerializerRegistry(serializer_settings)
    publisher = QueuePublisher(registry, backend=backend)
    publisher.publish("somequeue", {"message": "Mary"})
