import json
import uuid
from unittest.mock import MagicMock

from melange import DriverManager
from melange.messaging import MessagingDriver, ExchangeMessageConsumer, Message, \
    ExchangeListener, ExchangeMessagePublisher


class TestMessageConsumer:
    def test_consume_on_empty_queue(self):
        event_type_name = 'an_event_type_event'

        self._Scenario() \
            .given_an_empty_queue_to_listen() \
            .given_a_subscriber(listens_to=event_type_name) \
            .when_consuming_the_next_event_in_queue() \
            .then_the_subscriber_has_not_processed_any_event()

    def test_consume_on_queue_with_message(self):
        event_type_name = 'an_event_type_event'

        self._Scenario() \
            .given_a_queue_to_listen_with_an_event(event_of_type=event_type_name) \
            .given_a_subscriber(listens_to=event_type_name) \
            .when_consuming_the_next_event_in_queue() \
            .then_the_subscriber_has_processed_the_event() \
            .the_message_has_been_acknowledged()

    def test_consume_on_queue_with_message_but_subscriber_listens_to_different_events(self):
        event_type_name = 'an_event_type_event'
        event_type_name_2 = 'an_event_type_event_2'

        self._Scenario() \
            .given_a_queue_to_listen_with_an_event(event_of_type=event_type_name) \
            .given_a_subscriber(listens_to=event_type_name_2) \
            .when_consuming_the_next_event_in_queue() \
            .then_the_subscriber_has_not_processed_any_event() \
            .the_message_has_been_acknowledged()

    def test_unsubscribe(self):
        event_type_name = 'an_event_type_event'

        self._Scenario() \
            .given_a_queue_to_listen_with_an_event(event_of_type=event_type_name) \
            .given_a_subscriber(listens_to=event_type_name) \
            .when_unsubscribing_the_subscriber() \
            .when_consuming_the_next_event_in_queue() \
            .then_the_subscriber_has_not_processed_any_event() \
            .the_message_has_been_acknowledged()

    class _Scenario:
        def __init__(self):
            self.message_consumer = None
            self.subscriber = None
            self.event = None
            self.messages = None
            self.driver = MagicMock(spec=MessagingDriver)
            DriverManager.instance().use_driver(driver=self.driver)

        def given_a_queue_to_listen_with_an_event(self, event_of_type=None):
            self.messages = [self._create_message(i) for i in range(1)]
            queue = self._create_queue(self.messages)
            self.driver.declare_queue.return_value = (queue, '')

            self.event = Message(uuid.uuid4(), {'event_type_name': event_of_type}, None)
            self.driver.retrieve_messages.return_value = [self.event]

            event_queue_name = 'a_queue_name'
            topic_to_subscribe = 'a_topic_name'
            self.message_consumer = ExchangeMessageConsumer(event_queue_name, topic_to_subscribe)

            return self

        def given_a_subscriber(self, listens_to=None):
            self.subscriber = MagicMock(spec=ExchangeListener)
            self.subscriber.listens_to.return_value = listens_to

            self.message_consumer.subscribe(self.subscriber)

            return self

        def when_consuming_the_next_event_in_queue(self):
            self.message_consumer.consume_event()

            return self

        def then_the_subscriber_has_processed_the_event(self):
            self.subscriber.process_event.assert_called()
            return self

        def the_message_has_been_acknowledged(self):
            self.driver.acknowledge.assert_called()

            return self

        def given_an_empty_queue_to_listen(self):
            queue = self._create_queue()
            self.driver.declare_queue = MagicMock(return_value=(queue, ''))
            self.driver.declare_topic = MagicMock()

            event_queue_name = 'a_queue_name'
            topic_to_subscribe = 'a_topic_name'
            self.message_consumer = ExchangeMessageConsumer(event_queue_name, topic_to_subscribe)

            return self

        def then_the_subscriber_has_not_processed_any_event(self):
            self.subscriber.process.assert_not_called()
            return self

        def _create_queue(self, messages=[]):
            queue = MagicMock()

            self.driver.retrieve_messages.return_value = messages

            return queue

        def _create_message(self, i):
            message = MagicMock()
            message.body = json.dumps({
                'event_type_name': 'an_event_name'
            })
            return message

        def when_unsubscribing_the_subscriber(self):
            self.message_consumer.unsubscribe(self.subscriber)
            return self


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


class TestMessageConsumerRabbitMQ:
    def setup_method(self, m):
        self.exchange_consumer = None
        DriverManager.instance().use_driver(driver_name='rabbitMQ',
                                            host='localhost')
        self.driver = DriverManager.instance().get_driver()

    def teardown_method(self):
        if self.exchange_consumer._topics:
            for topic in self.exchange_consumer._topics:
                self.driver.delete_topic(topic)

        if self.exchange_consumer._event_queue:
            self.driver.delete_queue(self.exchange_consumer._event_queue)

        if self.exchange_consumer._dead_letter_queue:
            self.driver.delete_queue(self.exchange_consumer._dead_letter_queue)

    def test_consume_event_from_queue(self):
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
        return 'test_topic_{}'.format(uuid.uuid4())
