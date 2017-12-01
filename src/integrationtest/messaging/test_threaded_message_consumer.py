'''Tests for eventbus operations '''

import uuid
from time import sleep

from melange.messaging import ExchangeListener, ThreadedExchangeMessageConsumer
from melange.messaging.exchange_message_publisher import ExchangeMessagePublisher


class SubscriberMine(ExchangeListener):
    def __init__(self):
        self.processed_events = []

    def process(self, event, **kwargs):
        event['status'] = 'processed'
        self.processed_events.append(event)

    def listens_to(self):
        return 'EventMine'

    def get_processed_events(self):
        return self.processed_events


class TestThreadedMessageConsumer:
    def setup_method(self, m):
        self.NUM_EVENTS_TO_PUBLISH = 10

    def teardown_method(self):
        self.exchange_consumer.shutdown()

        if self.exchange_consumer:
            if self.exchange_consumer._event_queue:
                self.exchange_consumer._event_queue.delete()
            if self.exchange_consumer._dead_letter_queue:
                self.exchange_consumer._dead_letter_queue.delete()
            if self.exchange_consumer._topic:
                self.exchange_consumer._topic.delete()

    def test_handle_events_in_separate_thread(self):
        topic_name = self._get_topic_name()

        self.exchange_consumer = ThreadedExchangeMessageConsumer(event_queue_name=self._get_queue_name(),
                                                                 topic_to_subscribe=topic_name)

        subscriber = SubscriberMine()
        self.exchange_consumer.subscribe(subscriber)
        self.exchange_consumer.start()

        message_publisher = ExchangeMessagePublisher(topic=topic_name)

        for i in range(self.NUM_EVENTS_TO_PUBLISH):
            message_publisher.publish({'status': 'notprocessed'}, event_type_name='EventMine')

        sleep(4)

        processed_events = subscriber.get_processed_events()
        assert len(processed_events) == self.NUM_EVENTS_TO_PUBLISH and all(
            ev['status'] == 'processed' for ev in processed_events)

    def _get_queue_name(self):
        return 'test_queue_{}'.format(uuid.uuid4())

    def _get_topic_name(self):
        return 'test_queue_{}'.format(uuid.uuid4())
