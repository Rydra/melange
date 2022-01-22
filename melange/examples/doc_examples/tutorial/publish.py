from melange.backends.sqs.localsqs import LocalSQSBackend
from melange.publishers import QueuePublisher
from melange.serializers.pickle import PickleSerializer


class MyTestMessage:
    def __init__(self, message: str) -> None:
        self.message = message


if __name__ == "__main__":
    backend = LocalSQSBackend(host="localhost", port=9324)
    serializer = PickleSerializer()
    publisher = QueuePublisher(serializer, backend)
    message = MyTestMessage("Hello World!")
    publisher.publish("melangetutorial-queue", message)
    print("Message sent successfully!")
