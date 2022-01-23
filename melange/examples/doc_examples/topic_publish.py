from melange.backends.sqs.localsqs import LocalSQSBackend
from melange.examples.shared import serializer_registry
from melange.publishers import TopicPublisher
from melange.serializers.pickle import PickleSerializer


class MyTestMessage:
    def __init__(self, message: str) -> None:
        self.message = message


if __name__ == "__main__":
    backend = LocalSQSBackend(host="localhost", port=9324)
    serializer = PickleSerializer()
    publisher = TopicPublisher(serializer_registry, backend)
    message = MyTestMessage("Hello World!")
    publisher.publish("melangetutorial-topic", message)
    print("Message sent successfully!")
