from unittest.mock import MagicMock

from melange.aws.exchange_message_publisher import ExchangeMessagePublisher
from melange.aws.aws_manager import AWSManager
from melange.messaging.event_serializer import EventSerializer
from melange.messaging.eventmessage import EventMessage, EventSchema


class TestMessagePublisher:
    def test_publish_a_message(self):
        a_topic = 'a_topic'
        EventSerializer.instance().register(EventSchema)
        event = EventMessage()

        response = {'MessageId': '12345'}

        topic = MagicMock()
        topic.publish.return_value = response
        AWSManager.declare_topic = MagicMock(return_value=topic)

        message_publisher = ExchangeMessagePublisher(a_topic)
        success = message_publisher.publish(event)

        assert success
        topic.publish.assert_called()
