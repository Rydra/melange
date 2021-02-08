from melange.drivers.driver_manager import DriverManager
from melange.drivers.aws.aws_driver import AWSDriver
from melange.drivers.rabbitmq.rabbitmq_driver import RabbitMQDriver

DriverManager().add_available_drivers(aws=AWSDriver, rabbitMQ=RabbitMQDriver)
