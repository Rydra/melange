'''Tests for eventbus operations '''

import logging
import sys
import unittest
from signal import signal, SIGTERM, SIGINT
from threading import Lock
from time import sleep

from marshmallow import fields, post_load

from geeteventbus.aws.sqs_eventbus import SQSEventBus
from geeteventbus.event import Event, EventSchema
from geeteventbus.subscriber import subscriber

ebus = None


class EventMineSchema(EventSchema):
    data = fields.Dict()
    id = fields.Integer()

    @post_load
    def create_event_mine(self, data):
        return EventMine(data['topic'], data['data'], data['id'])


class EventMine(Event):
    event_type_name = 'event_mine'

    def __init__(self, topic, data, id):
        Event.__init__(self, topic, self.event_type_name)
        self.data = data
        self.id = id

    def set_status(self, status):
        self.data['status'] = status

    def get_status(self):
        return self.data['status']

    def get_id(self):
        return self.id


class SubscriberMine(subscriber):
    def __init__(self):
        super().__init__()
        print('Test subscriber initialized')
        self.processed_events = []

    def process(self, event):
        event.set_status('processed')
        self.processed_events.append(event)

    def listens_to(self):
        return EventMine.event_type_name

    def get_processed_events(self):
        return self.processed_events[:]


class TestRunner(unittest.TestCase):
    def setUp(self):
        print('Setting up')
        self.topic = 'dev-test-topic'
        self.events = [EventMine(self.topic, {'status': 'notprocessed'}, i) for i in range(50)]
        self.ebus = SQSEventBus(
            event_serializer_map={EventMine.event_type_name: EventMineSchema()},
            event_queue_name='dev-test-queue',
            topic_to_subscribe=self.topic)

        self.subscriber = SubscriberMine()

    def tearDown(self):
        self.ebus.shutdown()
        self.ebus = None
        self.events = None
        self.ordered_events = None
        self.subscriber = None

    def alltests(self):
        self.ebus.subscribe(self.subscriber)
        for ev in self.events:
            self.ebus.publish(ev)

        sleep(3)

        processed_events = self.subscriber.get_processed_events()

        return len(processed_events) == 50 and all(ev.get_status() == 'processed' for ev in processed_events)

    def test_sqs_eventbus(self):
        success = self.alltests()
        self.assertTrue(success)


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
