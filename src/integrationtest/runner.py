'''Tests for eventbus operations '''

import unittest
from threading import Lock, Thread
from time import sleep

from melange.domain_event_bus.domain_event_bus import DomainEventBus
from melange.domain_event_bus.domain_subscriber import DomainSubscriber
from melange.messaging.eventmessage import EventMessage

ebus = None


class event_mine(EventMessage):
    event_type_name = 'event_mine'

    def __init__(self, data, ident):
        EventMessage.__init__(self)
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


class subscriber_mine(DomainSubscriber):
    def __init__(self):
        self.processed_events = []
        self.lock = Lock()

    def process(self, event):
        event.set_status('processed')
        with self.lock:
            self.processed_events.append(event)

    def get_processed_events(self):
        with self.lock:
            ret = self.processed_events[:]
            return ret


class ThreadedDomainEventBus(Thread):
    def __init__(self):
        super().__init__()

    def run(self):
        print('hey yo')
        DomainEventBus.instance().reset()
        self.subscriber = subscriber_mine()
        self.events = []

        i = 0
        while i < 100:
            self.events.append(event_mine({'status': 'notprocessed'}, i))
            i += 1

        DomainEventBus.instance().subscribe(self.subscriber)
        for ev in self.events:
            DomainEventBus.instance().publish(ev)

        processed_events = self.subscriber.get_processed_events()

        assert len(processed_events) == 100

        for ev in processed_events:
            assert ev.get_status() == 'processed'

        print('Cool! Done!')


class test_runner(unittest.TestCase):
    def setUp(self):
        print('Setting up')
        self.events = []
        self.ebus = None

        i = 0
        while i < 100:
            self.events.append(event_mine({'status': 'notprocessed'}, i))
            i += 1

        self.subscriber = subscriber_mine()

    def tearDown(self):
        self.ebus = None
        self.events = None
        self.subscriber = None

        # def test_asynchronus_eventbus(self):
        #    self.ebus = EventBusFactory.create(subscribers_thread_safe=False)

    #
    #    self.ebus.subscribe(self.subscriber)
    #    for ev in self.events:
    #        self.ebus.publish(ev, self.topic)
    #
    #    sleep(2)
    #    processed_events = self.subscriber.get_processed_events()
    #
    #    assert len(processed_events) == 100
    #
    #    for ev in processed_events:
    #        assert ev.get_status() == 'processed'

    # def test_synchronus_eventbus(self):
    #
    #    self.ebus = EventBusFactory.create(synchronous=True)
    #
    #    self.ebus.subscribe(self.subscriber)
    #    for ev in self.events:
    #        self.ebus.publish(ev)
    #
    #    processed_events = self.subscriber.get_processed_events()
    #
    #    assert len(processed_events) == 100
    #
    #    for ev in processed_events:
    #        assert ev.get_status() == 'processed'

    def test_synchronus_eventbus_with_threads(self):
        DomainEventBus.instance().subscribe(self.subscriber)
        thread1 = ThreadedDomainEventBus()
        thread2 = ThreadedDomainEventBus()
        thread1.start()
        thread2.start()

        sleep(10)
        a = 1


# def interuppt_handler(signo, statck):
#    if ebus is not None:
#        try:
#            ebus.shutdown()
#        except Exception as e:
#            logging.error(e)
#            pass
#        sys.exit(1)


if __name__ == '__main__':
    # signal(SIGTERM, interuppt_handler)
    # signal(SIGINT, interuppt_handler)
    unittest.main()
    sleep(2)
