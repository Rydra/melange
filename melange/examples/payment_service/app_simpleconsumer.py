import os

from melange import QueuePublisher, SimpleMessageDispatcher
from melange.backends import LocalSQSBackend
from melange.examples.payment_service.consumer import PaymentConsumer
from melange.examples.payment_service.publisher import PaymentPublisher
from melange.examples.payment_service.repository import PaymentRepository
from melange.examples.payment_service.service import PaymentService
from melange.examples.shared import serializer_registry
from melange.serializers import PickleSerializer

if __name__ == "__main__":
    serializer = PickleSerializer()
    backend = LocalSQSBackend(
        host=os.environ.get("SQSHOST"), port=os.environ.get("SQSPORT")
    )

    payment_consumer = SimpleMessageDispatcher(
        PaymentConsumer(
            PaymentService(
                PaymentRepository(),
                PaymentPublisher(QueuePublisher(serializer_registry, backend=backend)),
            )
        ),
        serializer_registry,
        backend=backend,
    )

    print("Consuming...")
    payment_consumer.consume_loop("payment-updates")
