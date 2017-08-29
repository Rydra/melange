import logging

from geeteventbus.aws.messaging_manager import MessagingManager
from geeteventbus.event import Event


class MessagePublisher:
    def __init__(self, event_serializer):
        super().__init__()

        self.event_serializer = event_serializer

    def publish(self, event):

        if not isinstance(event, Event):
            logging.error('Invalid data passed. You must pass an event instance')
            return False

        topic = MessagingManager.declare_topic(event.get_topic())

        response = topic.publish(Message=self.event_serializer.serialize(event))

        if 'MessageId' not in response:
            raise ConnectionError('Could not send the event to the SNS TOPIC')

        return True