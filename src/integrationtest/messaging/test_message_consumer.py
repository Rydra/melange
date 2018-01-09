import uuid

from melange import DriverManager
from melange.messaging.exchange_listener import ExchangeListener
from melange.messaging.exchange_message_consumer import ExchangeMessageConsumer
from melange.messaging.exchange_message_publisher import ExchangeMessagePublisher


class TestMessageConsumer:
    def setup_method(self, m):
        self.exchange_consumer = None
        DriverManager.instance().use_driver(driver_name='aws')

    def teardown_method(self):
        driver = DriverManager.instance().get_driver()
        if self.exchange_consumer:
            if self.exchange_consumer._event_queue:
                driver.delete_queue(self.exchange_consumer._event_queue)
            if self.exchange_consumer._dead_letter_queue:
                driver.delete_queue(self.exchange_consumer._dead_letter_queue)
            if self.exchange_consumer._topics:
                for topic in self.exchange_consumer._topics:
                    driver.delete_topic(topic)

    def test_consume_event_from_sqs(self):
        topic_name = self._get_topic_name()
        self.exchange_consumer = ExchangeMessageConsumer(self._get_queue_name(),
                                                         topic_name)
        exchange_publisher = ExchangeMessagePublisher(topic=topic_name)

        self.listened_event = None

        class TestListener(ExchangeListener):
            def process(x, event, **kwargs):
                self.listened_event = event

            def listens_to(self):
                return ['TestEvent']

        self.exchange_consumer.subscribe(TestListener())
        exchange_publisher.publish({'value': 'somevalue'}, event_type_name='TestEvent')

        self.exchange_consumer.consume_event()
        assert self.listened_event['value'] == 'somevalue'
        assert self.listened_event['event_type_name'] == 'TestEvent'

    def test_consume_event_with_listeners_that_listen_multiple_events(self):
        topic_name = self._get_topic_name()
        self.exchange_consumer = ExchangeMessageConsumer(self._get_queue_name(),
                                                         topic_name)
        exchange_publisher = ExchangeMessagePublisher(topic=topic_name)

        self.listened_events = set()

        class TestListener(ExchangeListener):
            def process(x, event, **kwargs):
                self.listened_events.add(event['value'])

            def listens_to(x):
                return ['TestEvent', 'TestEvent2', 'TestEvent3']

        self.exchange_consumer.subscribe(TestListener())
        exchange_publisher.publish({'value': 'somevalue'}, event_type_name='TestEvent')
        exchange_publisher.publish({'value': 'somevalue2', 'event_type_name': 'TestEvent2'})
        exchange_publisher.publish({'value': 'somevalue3'}, event_type_name='TestEvent4')
        exchange_publisher.publish({'value': 'somevalue4'}, event_type_name='TestEvent3')

        self.exchange_consumer.consume_event()
        self.exchange_consumer.consume_event()
        self.exchange_consumer.consume_event()
        self.exchange_consumer.consume_event()

        assert len(self.listened_events) == 3
        assert 'somevalue' in self.listened_events
        assert 'somevalue2' in self.listened_events
        assert 'somevalue4' in self.listened_events
        assert 'somevalue3' not in self.listened_events

    def _get_queue_name(self):
        return 'test_queue_{}'.format(uuid.uuid4())

    def _get_topic_name(self):
        return 'test_queue_{}'.format(uuid.uuid4())
