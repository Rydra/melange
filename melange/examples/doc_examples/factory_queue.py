from melange.backends.factory import MessagingBackendFactory
from melange.backends.sqs.localsqs import LocalSQSBackend

backend = LocalSQSBackend()
factory = MessagingBackendFactory(backend)
factory.init_queue("payment-updates.fifo")
