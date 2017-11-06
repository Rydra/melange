import json
import logging

from melange.aws.event_serializer import EventSerializer
from melange.aws.eventmessage import EventMessage
from melange.aws.messaging_manager import MessagingManager


class ExchangeMessagePublisher:
    def __init__(self, topic):
        self.topic = MessagingManager.declare_topic(topic)

    def publish(self, event, event_type_name=None):

        if not isinstance(event, EventMessage) and not isinstance(event, dict):
            logging.error('Invalid data passed. You must pass an event instance or a dict')
            raise Exception('Invalid data passed. You must pass an event instance or a dict')

        if isinstance(event, dict) and 'event_type_name' not in event:
            raise Exception('When passing an event as a dict it has to include at least the event_type_name property')

        if isinstance(event, EventMessage):
            content = EventSerializer.instance().serialize(event)
        else:
            content = json.dumps(event)

        if event_type_name and isinstance(event_type_name, str):
            content['event_type_name'] = event_type_name

        response = self.topic.publish(Message=content)

        if 'MessageId' not in response:
            raise ConnectionError('Could not send the event to the SNS TOPIC')

        return True
