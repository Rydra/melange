from melange.backends.backend_manager import BackendManager
from melange.backends.sqs.localsqs import LocalSQSBackend
from melange.examples.shared import serializer_registry
from melange.publishers import QueuePublisher
from melange.serializers.pickle import PickleSerializer


class MyTestMessage:
    def __init__(self, message: str) -> None:
        self.message = message


if __name__ == "__main__":
    backend = LocalSQSBackend(host="localhost", port=9324)
    serializer = PickleSerializer()
    BackendManager().set_default_backend(backend)

    publisher = QueuePublisher(serializer_registry)
    message = MyTestMessage("Hello World!")
    publisher.publish("melangetutorial-queue", message)
    print("Message sent successfully!")
