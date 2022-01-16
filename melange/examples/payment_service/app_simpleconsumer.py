import os

from melange.backends.sqs.elasticmq import ElasticMQBackend
from melange.examples.common.serializer import PickleSerializer
from melange.examples.payment_service.consumer import PaymentSimpleConsumer
from melange.examples.payment_service.publisher import PaymentPublisher
from melange.examples.payment_service.repository import PaymentRepository
from melange.examples.payment_service.service import PaymentService
from melange.message_publisher import SQSPublisher

if __name__ == "__main__":
    serializer = PickleSerializer()
    backend = ElasticMQBackend(
        host=os.environ.get("SQSHOST"), port=os.environ.get("SQSPORT")
    )

    payment_consumer = PaymentSimpleConsumer(
        PaymentService(
            PaymentRepository(),
            PaymentPublisher(SQSPublisher(serializer, backend=backend)),
        ),
        PickleSerializer(),
        backend=backend,
    )

    print("Consuming...")
    payment_consumer.consume_loop("payment-updates")
