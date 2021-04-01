import json
import uuid
from typing import Any, Optional
from unittest.mock import MagicMock

import pytest
from bunch import Bunch
from hamcrest import *
from pytest_tools import pipe, scenariostep

from melange import DriverManager
from melange.drivers import configure_exchange
from melange.drivers.interfaces import MessagingDriver, Message
from melange.event_serializer import MessageSerializer
from melange.exchange_listener import ExchangeListener, listener
from melange.exchange_message_consumer import ExchangeMessageConsumer
from melange.exchange_message_publisher import ExchangeMessagePublisher, SQSPublisher


class TestEventSerializer(MessageSerializer):
    def manifest(self, data: Any) -> str:
        return "BananaEvent"

    def serialize(self, data: Any) -> str:
        if isinstance(data, BananaEvent):
            return json.dumps({"value": data.somevalue})
        return "apple"

    def deserialize(self, serialized_data: str, manifest: Optional[str] = None) -> Any:
        if serialized_data != "apple":
            data = json.loads(serialized_data)
            return BananaEvent(somevalue=data["value"])


class BananaEvent:
    def __init__(self, somevalue):
        self.somevalue = somevalue


class TestMessageConsumer:
    def test_consume_on_empty_queue(self, testcontext):
        event_type_name = "an_event_type_event"

        pipe(
            testcontext,
            given_an_empty_queue_to_listen(),
            given_a_subscriber(listens_to=event_type_name),
            when_consuming_the_next_event_in_queue(),
            then_the_subscriber_has_not_processed_any_event(),
        )

    def test_consume_on_queue_with_message(self):
        event_type_name = "an_event_type_event"

        self._Scenario().given_a_queue_to_listen_with_an_event(
            event_of_type=event_type_name
        ).given_a_subscriber(
            listens_to=event_type_name
        ).when_consuming_the_next_event_in_queue().then_the_subscriber_has_processed_the_event().the_message_has_been_acknowledged()

    def test_consume_on_queue_with_message_but_subscriber_listens_to_different_events(
        self,
    ):
        event_type_name = "an_event_type_event"
        event_type_name_2 = "an_event_type_event_2"

        self._Scenario().given_a_queue_to_listen_with_an_event(
            event_of_type=event_type_name
        ).given_a_subscriber(
            listens_to=event_type_name_2
        ).when_consuming_the_next_event_in_queue().then_the_subscriber_has_not_processed_any_event().the_message_has_been_acknowledged()

    def test_unsubscribe(self):
        event_type_name = "an_event_type_event"

        self._Scenario().given_a_queue_to_listen_with_an_event(
            event_of_type=event_type_name
        ).given_a_subscriber(
            listens_to=event_type_name
        ).when_unsubscribing_the_subscriber().when_consuming_the_next_event_in_queue().then_the_subscriber_has_not_processed_any_event().the_message_has_been_acknowledged()

    class _Scenario:
        def __init__(self):
            self.message_consumer = None
            self.subscriber = None
            self.event = None
            self.messages = None
            self.driver = MagicMock(spec=MessagingDriver)
            DriverManager().use_driver(driver=self.driver)

        def given_a_queue_to_listen_with_an_event(self, event_of_type=None):
            self.messages = [self._create_message(i) for i in range(1)]
            queue = self._create_queue(self.messages)
            self.driver.declare_queue.return_value = (queue, "")

            self.event = Message(uuid.uuid4(), {"event_type_name": event_of_type}, None)
            self.driver.retrieve_messages.return_value = [self.event]

            event_queue_name = "a_queue_name"
            topic_to_subscribe = "a_topic_name"
            self.message_consumer = ExchangeMessageConsumer(
                event_queue_name, TestEventSerializer(), topic_to_subscribe
            )

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
            self.driver.declare_queue = MagicMock(return_value=(queue, ""))
            self.driver.declare_topic = MagicMock()

            event_queue_name = "a_queue_name"
            topic_to_subscribe = "a_topic_name"
            self.message_consumer = ExchangeMessageConsumer(
                event_queue_name, TestEventSerializer(), topic_to_subscribe
            )

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
            message.body = json.dumps({"event_type_name": "an_event_name"})
            return message

        def when_unsubscribing_the_subscriber(self):
            self.message_consumer.unsubscribe(self.subscriber)
            return self


class TestMessageConsumerWithAWS:
    @pytest.fixture(autouse=True)
    def setup(self, request):
        self.exchange_consumer = None
        configure_exchange("aws")

        def teardown():
            driver = DriverManager().get_driver()
            if self.exchange_consumer:
                if self.exchange_consumer._event_queue:
                    driver.delete_queue(self.exchange_consumer._event_queue)
                if self.exchange_consumer._dead_letter_queue:
                    driver.delete_queue(self.exchange_consumer._dead_letter_queue)
                if self.exchange_consumer._topics:
                    for topic in self.exchange_consumer._topics:
                        driver.delete_topic(topic)

        request.addfinalizer(teardown)

    def test_consume_event_from_sqs(self):
        topic_name = self._get_topic_name()
        serializer = TestEventSerializer()
        self.exchange_consumer = ExchangeMessageConsumer(
            self._get_queue_name(), serializer, topic_name
        )
        exchange_publisher = ExchangeMessagePublisher(
            topic=topic_name, message_serializer=serializer
        )

        class TestListener(ExchangeListener):
            def __init__(self):
                super().__init__()
                self.listened_event = None

            @listener
            def on_event(self, event: BananaEvent):
                self.listened_event = event

        test_listener = TestListener()
        self.exchange_consumer.subscribe(test_listener)
        exchange_publisher.publish(BananaEvent("somevalue"))

        self.exchange_consumer.consume_event()
        assert_that(test_listener.listened_event, is_(BananaEvent))
        assert_that(test_listener.listened_event.somevalue, is_("somevalue"))

    def test_consume_event_coming_from_the_sqs_publisher(self):
        topic_name = self._get_queue_name()
        serializer = TestEventSerializer()
        queue_name = self._get_queue_name()
        self.exchange_consumer = ExchangeMessageConsumer(
            queue_name, serializer, topic_name
        )
        queue_publisher = SQSPublisher(
            queue_name=queue_name, message_serializer=serializer
        )

        class TestListener(ExchangeListener):
            def __init__(self):
                super().__init__()
                self.listened_event = None

            @listener
            def on_event(self, event: BananaEvent):
                self.listened_event = event

        test_listener = TestListener()
        self.exchange_consumer.subscribe(test_listener)
        queue_publisher.publish(BananaEvent("somevalue"))

        self.exchange_consumer.consume_event()
        assert_that(test_listener.listened_event, is_(BananaEvent))
        assert_that(test_listener.listened_event.somevalue, is_("somevalue"))

    def test_consume_event_with_listeners_that_listen_multiple_events(self):
        topic_name = self._get_topic_name()
        self.exchange_consumer = ExchangeMessageConsumer(
            self._get_queue_name(), TestEventSerializer(), topic_name
        )
        exchange_publisher = ExchangeMessagePublisher(
            topic=topic_name, message_serializer=TestEventSerializer()
        )

        self.listened_events = set()

        class TestListener(ExchangeListener):
            def __init__(self):
                super().__init__(None)

            def process(x, event, **kwargs):
                self.listened_events.add(event["value"])

            def listens_to(x):
                return ["TestEvent", "TestEvent2", "TestEvent3"]

        self.exchange_consumer.subscribe(TestListener())
        exchange_publisher.publish({"value": "somevalue"})
        exchange_publisher.publish(
            {"value": "somevalue2", "event_type_name": "TestEvent2"}
        )
        exchange_publisher.publish({"value": "somevalue3"})
        exchange_publisher.publish({"value": "somevalue4"})

        self.exchange_consumer.consume_event()
        self.exchange_consumer.consume_event()
        self.exchange_consumer.consume_event()
        self.exchange_consumer.consume_event()

        assert len(self.listened_events) == 3
        assert "somevalue" in self.listened_events
        assert "somevalue2" in self.listened_events
        assert "somevalue4" in self.listened_events
        assert "somevalue3" not in self.listened_events

    def _get_queue_name(self):
        return "test_queue_{}".format(uuid.uuid4())

    def _get_topic_name(self):
        return "test_queue_{}".format(uuid.uuid4())


@pytest.fixture
def testcontext():
    driver = MagicMock(spec=MessagingDriver)
    DriverManager().use_driver(driver=driver)
    return Bunch(
        message_consumer=None, subscriber=None, event=None, messages=None, driver=driver
    )


def given_a_queue_to_listen_with_an_event(self, event_of_type=None):
    self.messages = [self._create_message(i) for i in range(1)]
    queue = self._create_queue(self.messages)
    self.driver.declare_queue.return_value = (queue, "")

    self.event = Message(uuid.uuid4(), {"event_type_name": event_of_type}, None)
    self.driver.retrieve_messages.return_value = [self.event]

    event_queue_name = "a_queue_name"
    topic_to_subscribe = "a_topic_name"
    self.message_consumer = ExchangeMessageConsumer(
        event_queue_name, TestEventSerializer(), topic_to_subscribe
    )

    return self


@scenariostep
def given_a_subscriber(ctx, listens_to=None):
    ctx.subscriber = MagicMock(spec=ExchangeListener)
    ctx.subscriber.listens_to.return_value = listens_to

    ctx.message_consumer.subscribe(ctx.subscriber)

    return ctx


@scenariostep
def when_consuming_the_next_event_in_queue(ctx):
    ctx.message_consumer.consume_event()

    return ctx


def then_the_subscriber_has_processed_the_event(self):
    self.subscriber.process_event.assert_called()
    return self


def the_message_has_been_acknowledged(self):
    self.driver.acknowledge.assert_called()

    return self


@scenariostep
def given_an_empty_queue_to_listen(ctx):
    driver = ctx.driver
    queue = _create_queue(driver)
    driver.declare_queue = MagicMock(return_value=(queue, ""))
    driver.declare_topic = MagicMock()

    event_queue_name = "a_queue_name"
    topic_to_subscribe = "a_topic_name"
    ctx.message_consumer = ExchangeMessageConsumer(event_queue_name, topic_to_subscribe)

    return ctx


@scenariostep
def then_the_subscriber_has_not_processed_any_event(ctx):
    ctx.subscriber.process.assert_not_called()
    return ctx


def _create_queue(driver, messages=None):
    queue = MagicMock()

    driver.retrieve_messages.return_value = messages or []

    return queue


def _create_message(self, i):
    message = MagicMock()
    message.body = json.dumps({"event_type_name": "an_event_name"})
    return message


def when_unsubscribing_the_subscriber(self):
    self.message_consumer.unsubscribe(self.subscriber)


@pytest.mark.skip()
class TestMessageConsumerRabbitMQ:
    def setup_method(self, m):
        self.exchange_consumer = None
        DriverManager().use_driver(driver_name="rabbitMQ", host="localhost")
        self.driver = DriverManager().get_driver()

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
        self.exchange_consumer = ExchangeMessageConsumer(
            self._get_queue_name(), topic_name
        )
        exchange_publisher = ExchangeMessagePublisher(topic=topic_name)

        self.listened_event = None

        class TestListener(ExchangeListener):
            def process(x, event, **kwargs):
                self.listened_event = event

            def listens_to(self):
                return ["TestEvent"]

        self.exchange_consumer.subscribe(TestListener())
        exchange_publisher.publish({"value": "somevalue"}, manifest="TestEvent")

        self.exchange_consumer.consume_event()
        assert self.listened_event["value"] == "somevalue"
        assert self.listened_event["event_type_name"] == "TestEvent"

    def test_consume_event_with_listeners_that_listen_multiple_events(self):
        topic_name = self._get_topic_name()
        self.exchange_consumer = ExchangeMessageConsumer(
            self._get_queue_name(), topic_name
        )
        exchange_publisher = ExchangeMessagePublisher(topic=topic_name)

        self.listened_events = set()

        class TestListener(ExchangeListener):
            def process(x, event, **kwargs):
                self.listened_events.add(event["value"])

            def listens_to(x):
                return ["TestEvent", "TestEvent2", "TestEvent3"]

        self.exchange_consumer.subscribe(TestListener())
        exchange_publisher.publish({"value": "somevalue"}, manifest="TestEvent")
        exchange_publisher.publish(
            {"value": "somevalue2", "event_type_name": "TestEvent2"}
        )
        exchange_publisher.publish({"value": "somevalue3"}, manifest="TestEvent4")
        exchange_publisher.publish({"value": "somevalue4"}, manifest="TestEvent3")

        self.exchange_consumer.consume_event()
        self.exchange_consumer.consume_event()
        self.exchange_consumer.consume_event()
        self.exchange_consumer.consume_event()

        assert len(self.listened_events) == 3
        assert "somevalue" in self.listened_events
        assert "somevalue2" in self.listened_events
        assert "somevalue4" in self.listened_events
        assert "somevalue3" not in self.listened_events

    def _get_queue_name(self):
        return "test_queue_{}".format(uuid.uuid4())

    def _get_topic_name(self):
        return "test_topic_{}".format(uuid.uuid4())
