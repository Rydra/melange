import os

from melange.backends.sqs.elasticmq import ElasticMQBackend
from melange.examples.common.serializer import PickleSerializer
from melange.examples.saga_pattern.consumer import SagaConsumer
from melange.examples.saga_pattern.publisher import SagaPublisher
from melange.examples.saga_pattern.repository import SagaRepository
from melange.message_publisher import SQSPublisher

if __name__ == "__main__":
    serializer = PickleSerializer()
    backend = ElasticMQBackend(
        host=os.environ.get("SQSHOST"), port=os.environ.get("SQSPORT")
    )

    payment_consumer = SagaConsumer(
        SagaRepository(),
        SagaPublisher(SQSPublisher(serializer, backend)),
        message_serializer=PickleSerializer(),
        backend=backend,
        always_ack=True,
    )

    print("Consuming...")
    payment_consumer.consume_loop("saga-updates")
