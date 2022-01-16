from unittest.mock import MagicMock

from melange.messaging import BackendManager, ExchangeMessagePublisher, MessagingBackend


class TestMessagePublisher:
    def test_publish_a_message(self):
        a_topic = "a_topic"
        event = {"some_content": "12345"}

        backend = MagicMock(spec=MessagingBackend)
        BackendManager().use_backend(backend=backend)

        message_publisher = ExchangeMessagePublisher(a_topic)
        success = message_publisher.publish(event, manifest="some_event")

        assert success
        backend.publish.assert_called()
