'''Tests for eventbus operations '''

import logging
import sys
import unittest
from signal import signal, SIGTERM, SIGINT
from threading import Lock
from time import sleep

from melange.event import Event
from melange.eventbus_factory import EventBusFactory

from melange.subscriber import Subscriber

ebus = None


class event_mine(Event):
    def __init__(self, data, ident):
        Event.__init__(self)
        self.data = data
        self.id = ident

    def set_status(self, status):
        self.data['status'] = status

    def get_status(self):
        return self.data['status']

    def set_id(self, ident):
        self.id = ident

    def get_id(self):
        return self.id


class subuscriber_mine(Subscriber):
    def __init__(self, topic):
        super().__init__(topic)
        print('Test subscriber initialized')
        self.processed_events = []
        self.lock = Lock()

    def process(self, event):
        event.set_status('processed')
        with self.lock:
            self.processed_events.append(event)

    def listens_to(self):
        return Event.ALL

    def get_processed_events(self):
        with self.lock:
            ret = self.processed_events[:]
            return ret


class test_runner(unittest.TestCase):
    def setUp(self):
        print('Setting up')
        self.topic = 'topic'
        self.events = []
        self.ebus = None

        i = 0
        while i < 100:
            self.events.append(event_mine({'status': 'notprocessed'}, i))
            i += 1

        self.subscriber = subuscriber_mine(self.topic)

    def tearDown(self):
        self.ebus.shutdown()
        self.ebus = None
        self.events = None
        self.subscriber = None

    def test_asynchronus_eventbus(self):
        self.ebus = EventBusFactory.create(subscribers_thread_safe=False)

        self.ebus.subscribe(self.subscriber)
        for ev in self.events:
            self.ebus.publish(ev, self.topic)

        sleep(2)
        processed_events = self.subscriber.get_processed_events()

        assert len(processed_events) == 100

        for ev in processed_events:
            assert ev.get_status() == 'processed'

    def test_synchronus_eventbus(self):

        self.ebus = EventBusFactory.create(synchronous=True)

        self.ebus.subscribe(self.subscriber)
        for ev in self.events:
            self.ebus.publish(ev, self.topic)

        processed_events = self.subscriber.get_processed_events()

        assert len(processed_events) == 100

        for ev in processed_events:
            assert ev.get_status() == 'processed'


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
