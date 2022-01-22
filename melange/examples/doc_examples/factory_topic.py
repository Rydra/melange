from melange.backends.factory import MessagingBackendFactory
from melange.backends.sqs.sqs_backend import AWSBackend

backend = AWSBackend()
factory = MessagingBackendFactory(backend)
factory.init_topic("my-topic")
