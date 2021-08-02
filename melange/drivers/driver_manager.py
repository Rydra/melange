from typing import Dict, Type, Any

from singleton import Singleton

from melange.drivers.interfaces import MessagingDriver


class DriverManager(metaclass=Singleton):
    """
    This class should be used to initialize the type of messaging provider you
    want to use (Rabbit, AWS, etc)
    """

    def __init__(self):
        self._driver = None
        self._drivers: Dict[str, Any] = {}

    def add_available_drivers(self, **kwargs):
        self._drivers.update(kwargs)

    def use_driver(self, driver: MessagingDriver = None, driver_name=None, **kwargs):
        if driver:
            if not isinstance(driver, MessagingDriver):
                raise Exception("Invalid driver supplied")

            self._driver = driver

        elif driver_name:
            driver = self._drivers.get(driver_name)
            if not driver:
                raise Exception("Invalid driver supplied")

            self._driver = driver(**kwargs)

        else:
            raise Exception("You need to either supply a driver or a driver_name!")

    def get_driver(self):
        if not self._driver:
            raise Exception(
                "No driver is registered. Please call 'use_driver' prior to getting it"
            )

        return self._driver
