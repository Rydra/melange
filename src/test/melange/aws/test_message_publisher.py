from unittest.mock import MagicMock

from melange.messaging.event_serializer import EventSerializer
from melange.messaging.event_message import EventMessage, EventSchema
from melange.messaging.exchange_message_publisher import ExchangeMessagePublisher


class TestMessagePublisher:
    def test_publish_a_message(self):
        a_topic = 'a_topic'
        EventSerializer.instance().register(EventSchema)
        event = EventMessage()

        response = {'MessageId': '12345'}

        driver = MagicMock()
        topic = MagicMock()
        topic.publish.return_value = response
        driver.declare_topic = MagicMock(return_value=topic)

        message_publisher = ExchangeMessagePublisher(a_topic)
        success = message_publisher.publish(event)

        assert success
        topic.publish.assert_called()
