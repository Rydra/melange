import os

from melange.backends.sqs.localsqs import LocalSQSBackend
from melange.examples.payment_service.consumer import PaymentConsumer
from melange.examples.payment_service.publisher import PaymentPublisher
from melange.examples.payment_service.repository import PaymentRepository
from melange.examples.payment_service.service import PaymentService
from melange.examples.shared import serializer_registry
from melange.message_dispatcher import MessageDispatcher
from melange.publishers import QueuePublisher
from melange.serializers.pickle import PickleSerializer

if __name__ == "__main__":
    serializer = PickleSerializer()
    backend = LocalSQSBackend(
        host=os.environ.get("SQSHOST"), port=os.environ.get("SQSPORT")
    )

    dispatcher = MessageDispatcher(
        serializer_registry,
        backend=backend,
    )

    payment_consumer = PaymentConsumer(
        PaymentService(
            PaymentRepository(),
            PaymentPublisher(QueuePublisher(serializer_registry, backend=backend)),
        )
    )

    dispatcher.attach_consumer(payment_consumer)

    print("Consuming...")
    dispatcher.consume_loop("payment-updates")
