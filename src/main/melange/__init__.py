from melange.drivers.aws import AWSDriver
from melange.messaging.driver_manager import DriverManager

DriverManager.instance().add_available_drivers(aws=AWSDriver())
