from melange import MessagingBackendFactory
from melange.backends import LocalSQSBackend

backend = LocalSQSBackend(host="http://localhost", port=4566)
factory = MessagingBackendFactory(backend)
factory.init_queue("melangetutorial-queue")
