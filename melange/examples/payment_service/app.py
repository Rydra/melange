import os

from melange.backends.sqs.elasticmq import ElasticMQBackend
from melange.examples.payment_service.consumer import PaymentConsumer
from melange.examples.payment_service.publisher import PaymentPublisher
from melange.examples.payment_service.repository import PaymentRepository
from melange.examples.payment_service.service import PaymentService
from melange.message_dispatcher import ConsumerDispatcher
from melange.publishers import QueuePublisher
from melange.serializers.pickle import PickleSerializer

if __name__ == "__main__":
    serializer = PickleSerializer()
    backend = ElasticMQBackend(
        host=os.environ.get("SQSHOST"), port=os.environ.get("SQSPORT")
    )

    dispatcher = ConsumerDispatcher(
        PickleSerializer(),
        backend=backend,
    )

    payment_consumer = PaymentConsumer(
        PaymentService(
            PaymentRepository(),
            PaymentPublisher(QueuePublisher(serializer, backend=backend)),
        )
    )

    dispatcher.subscribe(payment_consumer)

    print("Consuming...")
    dispatcher.consume_loop("payment-updates")
