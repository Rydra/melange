import os

from melange.backends.factory import MessagingBackendFactory
from melange.backends.sqs.elasticmq import ElasticMQBackend

if __name__ == "__main__":
    backend = ElasticMQBackend(
        host=os.environ.get("SQSHOST"), port=os.environ.get("SQSPORT")
    )

    factory = MessagingBackendFactory(
        backend=backend,
    )
    factory.init_queue("payment-updates")

    print("Queues created.")
