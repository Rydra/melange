import os

from melange.backends.sqs.elasticmq import ElasticMQBackend
from melange.examples.saga_pattern.consumer import SagaConsumer
from melange.examples.saga_pattern.publisher import SagaPublisher
from melange.examples.saga_pattern.repository import SagaRepository
from melange.message_dispatcher import SimpleMessageDispatcher
from melange.publishers import QueuePublisher
from melange.serializers.pickle import PickleSerializer

if __name__ == "__main__":
    serializer = PickleSerializer()
    backend = ElasticMQBackend(
        host=os.environ.get("SQSHOST"), port=os.environ.get("SQSPORT")
    )

    payment_consumer = SagaConsumer(
        SagaRepository(),
        SagaPublisher(QueuePublisher(serializer, backend)),
    )

    print("Consuming...")
    consumer_handler = SimpleMessageDispatcher(
        payment_consumer,
        message_serializer=PickleSerializer(),
        backend=backend,
        always_ack=True,
    )
    consumer_handler.consume_loop("saga-updates")
