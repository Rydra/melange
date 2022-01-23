import os

from melange import MessagingBackendFactory
from melange.backends import LocalSQSBackend

if __name__ == "__main__":
    backend = LocalSQSBackend(
        host=os.environ.get("SQSHOST"), port=os.environ.get("SQSPORT")
    )

    factory = MessagingBackendFactory(
        backend=backend,
    )
    factory.init_queue("payment-updates")
    factory.init_queue("order-updates")
    factory.init_queue("saga-updates")

    print("Queues created.")
