from simple_cqrs.domain_event import DomainEvent

from melange.backends.sqs.localsqs import LocalSQSBackend
from melange.consumers import SingleDispatchConsumer, consumer
from melange.examples.doc_examples.tutorial.publish import MyTestMessage
from melange.message_dispatcher import SimpleMessageDispatcher
from melange.serializers.pickle import PickleSerializer
from melange.serializers.registry import SerializerRegistry


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
    serializer = PickleSerializer()
    consumer = MyConsumer()
    message_dispatcher = SimpleMessageDispatcher(
        consumer,
        serializer_registry,
        backend=backend,
    )
    print("Consuming...")
    message_dispatcher.consume_loop("melangetutorial-queue")
