from melange.drivers.aws import AWSDriver
from melange.drivers.rabbitmq_driver import RabbitMQDriver
from melange.messaging.driver_manager import DriverManager

DriverManager.instance().add_available_drivers(
    aws=AWSDriver, rabbitMQ=RabbitMQDriver)
