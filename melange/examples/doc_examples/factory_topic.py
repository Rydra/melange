from melange import MessagingBackendFactory
from melange.backends import AWSBackend

backend = AWSBackend()
factory = MessagingBackendFactory(backend)
factory.init_topic("my-topic")
