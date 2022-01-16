# type: ignore

from melange.backends.backend_manager import BackendManager
from melange.backends.rabbitmq.rabbitmq_backend import RabbitMQBackend
from melange.backends.sqs.sqs_backend import SQSBackend

BackendManager().add_available_backends(aws=SQSBackend, rabbitMQ=RabbitMQBackend)
