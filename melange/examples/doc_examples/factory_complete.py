from melange.backends.factory import MessagingBackendFactory
from melange.backends.sqs.localsqs import LocalSQSBackend

backend = LocalSQSBackend()
factory = MessagingBackendFactory(backend)
factory.init_queue(
    "payment-updates.fifo",
    ["my-topic-1", "my-topic-2", "my-topic-3"],
    dead_letter_queue_name="payment-updates.fifo",
)
