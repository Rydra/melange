'''Tests for eventbus operations '''

import logging
import sys
import unittest
from signal import signal, SIGTERM, SIGINT
from time import sleep

from marshmallow import fields, post_load

from melange.aws.exchange_message_consumer import ThreadedExchangeMessageConsumer
from melange.aws.exchange_message_publisher import ExchangeMessagePublisher
from melange.messaging.event_serializer import EventSerializer
from melange.messaging.eventmessage import EventMessage, EventSchema
from melange.messaging.exchange_listener import ExchangeListener

ebus = None

NUM_EVENTS_TO_PUBLISH = 10

class EventMineSchema(EventSchema):
    data = fields.Dict()
    id = fields.Integer()

    @post_load
    def create_event_mine(self, data):
        return EventMine(data['data'], data['id'])


class EventMine(EventMessage):
    event_type_name = 'EventMine'

    def __init__(self, data, id):
        EventMessage.__init__(self, self.event_type_name)
        self.data = data
        self.id = id

    def set_status(self, status):
        self.data['status'] = status

    def get_status(self):
        return self.data['status']

    def get_id(self):
        return self.id


class SubscriberMine(ExchangeListener):
    def __init__(self):
        print('Test subscriber initialized')
        self.processed_events = []

    def process(self, event, **kwargs):
        event.set_status('processed')
        self.processed_events.append(event)

    def listens_to(self):
        return EventMine.event_type_name

    def get_processed_events(self):
        return self.processed_events[:]


class TestRunner:
    def setup_method(self, m):
        print('Setting up')
        self.topic = 'dev-test-topic'
        self.events = [EventMine({'status': 'notprocessed'}, i) for i in range(NUM_EVENTS_TO_PUBLISH)]
        EventSerializer.instance().register(EventMineSchema, EventMineSchema)
        self.message_consumer = ThreadedExchangeMessageConsumer(
            event_queue_name='dev-test-queue',
            topic_to_subscribe=self.topic)

        self.message_consumer.start()

        self.subscriber = SubscriberMine()

    def teardown_method(self):
        self.message_consumer.shutdown()
        self.events = None
        self.ordered_events = None
        self.subscriber = None

    def alltests(self):
        self.message_consumer.subscribe(self.subscriber)
        message_publisher = ExchangeMessagePublisher(topic=self.topic)
        for ev in self.events:
            message_publisher.publish(ev)

        sleep(3)

        processed_events = self.subscriber.get_processed_events()

        return len(processed_events) == NUM_EVENTS_TO_PUBLISH and all(ev.get_status() == 'processed' for ev in processed_events)

    def test_sqs_eventbus(self):
        success = self.alltests()
        assert success

def interuppt_handler(signo, statck):
    if ebus is not None:
        try:
            ebus.shutdown()
        except Exception as e:
            logging.error(e)
            pass
        sys.exit(1)


if __name__ == '__main__':
    signal(SIGTERM, interuppt_handler)
    signal(SIGINT, interuppt_handler)
    unittest.main()
    sleep(2)
