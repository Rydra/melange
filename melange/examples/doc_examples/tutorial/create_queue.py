from melange.backends.factory import MessagingBackendFactory
from melange.backends.sqs.localsqs import LocalSQSBackend

backend = LocalSQSBackend(host="localhost", port=9324)
factory = MessagingBackendFactory(backend)
factory.init_queue("melangetutorial-queue")
