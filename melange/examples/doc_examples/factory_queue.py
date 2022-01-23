from melange import MessagingBackendFactory
from melange.backends import LocalSQSBackend

backend = LocalSQSBackend()
factory = MessagingBackendFactory(backend)
factory.init_queue("payment-updates.fifo")
