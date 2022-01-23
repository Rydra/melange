import os

from melange import QueuePublisher, SimpleMessageDispatcher
from melange.backends import LocalSQSBackend
from melange.examples.saga_pattern.consumer import SagaConsumer
from melange.examples.saga_pattern.publisher import SagaPublisher
from melange.examples.saga_pattern.repository import SagaRepository
from melange.examples.shared import serializer_registry
from melange.serializers import PickleSerializer

if __name__ == "__main__":
    serializer = PickleSerializer()
    backend = LocalSQSBackend(
        host=os.environ.get("SQSHOST"), port=os.environ.get("SQSPORT")
    )

    payment_consumer = SagaConsumer(
        SagaRepository(),
        SagaPublisher(QueuePublisher(serializer_registry, backend)),
    )

    print("Consuming...")
    consumer_handler = SimpleMessageDispatcher(
        payment_consumer,
        serializer_registry,
        backend=backend,
        always_ack=True,
    )
    consumer_handler.consume_loop("saga-updates")
