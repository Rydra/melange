import logging

from .event_serializer import EventMessage
from .event_serializer import EventSerializer
from .driver_manager import DriverManager


class ExchangeMessagePublisher:
    def __init__(self, topic, driver=None):
        self._driver = driver or DriverManager.instance().get_driver()
        self._topic = self._driver.declare_topic(topic)

    def publish(self, event, event_type_name=None):
        if not isinstance(event, EventMessage) and not isinstance(event, dict):
            logging.error('Invalid data passed. You must pass an event instance or a dict')
            raise Exception('Invalid data passed. You must pass an event instance or a dict')

        if not event_type_name and (isinstance(event, dict) and 'event_type_name' not in event):
            raise Exception('When passing an event as a dict it has to include at least the event_type_name property')

        if event_type_name and isinstance(event, dict):
            event['event_type_name'] = event_type_name

        content = EventSerializer.instance().serialize(event)

        self._driver.publish(content, self._topic)

        return True
