from melange.backends.testing import InMemoryMessagingBackend, link_synchronously
from melange.consumers import Consumer
from melange.publishers import QueuePublisher
from melange.serializers.pickle import PickleSerializer


def test_inmemory_messaging_backend():
    consumer_1 = Consumer(lambda message: print(f"Hello {message['message']}!"))
    consumer_2 = Consumer(lambda message: print(f"Hello {message['message']} 2!"))

    serializer = PickleSerializer()
    backend = InMemoryMessagingBackend()
    link_synchronously("somequeue", [consumer_1, consumer_2], serializer, backend)

    publisher = QueuePublisher(PickleSerializer(), backend=backend)
    publisher.publish("somequeue", {"message": "Mary"})
