import logging

from .aws_manager import AWSManager
from melange.messaging import EventSerializer
from melange.messaging import EventMessage


class ExchangeMessagePublisher:
    def __init__(self, topic):
        self.topic = AWSManager.declare_topic(topic)

    def publish(self, event, event_type_name=None):
        if not isinstance(event, EventMessage) and not isinstance(event, dict):
            logging.error('Invalid data passed. You must pass an event instance or a dict')
            raise Exception('Invalid data passed. You must pass an event instance or a dict')

        if not event_type_name and (isinstance(event, dict) and 'event_type_name' not in event):
            raise Exception('When passing an event as a dict it has to include at least the event_type_name property')

        if event_type_name and isinstance(event, dict):
            event['event_type_name'] = event_type_name

        content = EventSerializer.instance().serialize(event)

        response = self.topic.publish(Message=content)

        if 'MessageId' not in response:
            raise ConnectionError('Could not send the event to the SNS TOPIC')

        return True
