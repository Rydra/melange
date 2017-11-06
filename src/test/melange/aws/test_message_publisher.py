from unittest.mock import MagicMock

from melange.aws.event_serializer import EventSerializer
from melange.aws.eventmessage import EventMessage, EventSchema
from melange.aws.exchange_message_publisher import ExchangeMessagePublisher
from melange.aws.messaging_manager import MessagingManager


class TestMessagePublisher:
    def test_publish_a_message(self):

        a_topic = 'a_topic'
        EventSerializer.instance().register({EventMessage.event_type_name: EventSchema()})
        event = EventMessage(event_type_name=EventMessage.event_type_name)

        response = {'MessageId': '12345'}

        topic = MagicMock()
        topic.publish.return_value = response
        MessagingManager.declare_topic = MagicMock(return_value=topic)

        message_publisher = ExchangeMessagePublisher(a_topic)
        success = message_publisher.publish(event)

        assert success
        topic.publish.assert_called()
