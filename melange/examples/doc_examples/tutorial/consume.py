from simple_cqrs.domain_event import DomainEvent

from melange import SimpleMessageDispatcher, SingleDispatchConsumer, consumer
from melange.backends import LocalSQSBackend
from melange.examples.doc_examples.tutorial.publish import MyTestMessage
from melange.serializers import PickleSerializer, SerializerRegistry


class MyConsumer(SingleDispatchConsumer):
    @consumer
    def on_my_test_message_received(self, event: MyTestMessage) -> None:
        print(event.message)


if __name__ == "__main__":
    serializer_settings = {
        "serializers": {"pickle": PickleSerializer},
        "serializer_bindings": {DomainEvent: "pickle"},
    }

    serializer_registry = SerializerRegistry(serializer_settings)

    backend = LocalSQSBackend(host="localhost", port=9324)
    consumer = MyConsumer()
    message_dispatcher = SimpleMessageDispatcher(
        consumer,
        serializer_registry,
        backend=backend,
    )
    print("Consuming...")
    message_dispatcher.consume_loop("melangetutorial-queue")
