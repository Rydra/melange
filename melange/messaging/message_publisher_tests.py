from unittest.mock import MagicMock

from melange.messaging import MessagingDriver, DriverManager, ExchangeMessagePublisher


class TestMessagePublisher:
    def test_publish_a_message(self):
        a_topic = 'a_topic'
        event = {'some_content': '12345'}

        driver = MagicMock(spec=MessagingDriver)
        DriverManager.instance().use_driver(driver=driver)

        message_publisher = ExchangeMessagePublisher(a_topic)
        success = message_publisher.publish(event, event_type_name='some_event')

        assert success
        driver.publish.assert_called()
