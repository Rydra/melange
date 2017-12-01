from melange.drivers.aws import MessagingDriver, AWSDriver
from melange.infrastructure import Singleton


@Singleton
class DriverManager:

    def __init__(self):
        self._driver = None
        self._drivers = {
            'aws': AWSDriver()
        }

    def use_driver(self, driver_name=None, driver=None):
        if driver:
            if not isinstance(driver, MessagingDriver):
                raise Exception('Invalid driver supplied')

            self._driver = driver

        elif driver_name:
            driver = self._drivers.get(driver_name)
            if not driver:
                raise Exception('Invalid driver supplied')

            self._driver = driver

    def get_driver(self):
        if not self._driver:
            raise Exception('No driver is registered. Please call \'use_driver\' prior to getting it')

        return self._driver
