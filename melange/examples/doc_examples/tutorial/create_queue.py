from melange import MessagingBackendFactory
from melange.backends import LocalSQSBackend

backend = LocalSQSBackend(host="localhost", port=9324)
factory = MessagingBackendFactory(backend)
factory.init_queue("melangetutorial-queue")
