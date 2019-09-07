from threading import Thread

from melange.domain_event_bus import DomainEvent, DomainEventBus, DomainEventHandler
from melange.domain_event_bus.debugger import Debugger


class TestDomainEventBus:
    def test_publishing_and_receive_an_event(self):
        self.listened_event = None

        class TestDomainEvent(DomainEvent):
            pass

        class TestDomainSubscriber(DomainEventHandler):
            def process(x, event):
                nonlocal self
                self.listened_event = event

            def listens_to(x):
                return [DomainEvent]

        test_domain_event = TestDomainEvent()
        DomainEventBus.instance().reset()
        TestDomainSubscriber().listen()
        test_domain_event.emit()

        assert self.listened_event == test_domain_event

    def test_receive_all_event_types_if_listens_to_is_not_overriden(self):
        self.listened_events = []

        class TestDomainEvent(DomainEvent):
            pass

        class TestDomainEvent2(DomainEvent):
            pass

        class TestDomainSubscriber(DomainEventHandler):
            def process(x, event):
                nonlocal self
                self.listened_events.append(event)


        DomainEventBus.instance().reset()
        TestDomainSubscriber().listen()
        test_domain_event_1 = TestDomainEvent().emit()
        test_domain_event_2 = TestDomainEvent2().emit()
        test_domain_event_3 = TestDomainEvent().emit()
        test_domain_event_4 = TestDomainEvent2().emit()

        assert self.listened_events[0] == test_domain_event_1
        assert self.listened_events[1] == test_domain_event_2
        assert self.listened_events[2] == test_domain_event_3
        assert self.listened_events[3] == test_domain_event_4

    def test_receive_only_specifically_listened_events(self):
        self.listened_events_1 = []
        self.listened_events_2 = []

        class TestDomainEvent(DomainEvent):
            name = 'TestDomainEvent'

        class TestDomainEvent2(DomainEvent):
            name = 'TestDomainEvent2'

        class TestDomainEvent3(DomainEvent):
            name = 'TestDomainEvent3'

        class TestDomainSubscriber(DomainEventHandler):
            def process(x, event):
                nonlocal self
                self.listened_events_1.append(event)

            def listens_to(self):
                return [TestDomainEvent]

        class TestDomainSubscriber2(DomainEventHandler):
            def process(x, event):
                nonlocal self
                self.listened_events_2.append(event)

            def listens_to(self):
                return [TestDomainEvent2]


        DomainEventBus.instance().reset()
        TestDomainSubscriber().listen()
        TestDomainSubscriber2().listen()

        test_domain_event_1 = TestDomainEvent().emit()
        test_domain_event_2 = TestDomainEvent2().emit()
        test_domain_event_3 = TestDomainEvent().emit()
        TestDomainEvent3().emit()

        assert len(self.listened_events_1) == 2
        assert len(self.listened_events_2) == 1
        assert self.listened_events_1[0] == test_domain_event_1
        assert self.listened_events_1[1] == test_domain_event_3
        assert self.listened_events_2[0] == test_domain_event_2

    def test_the_domain_event_publisher_is_thread_bound(self):
        self.listened_events_1 = []
        self.listened_events_2 = []

        class TestDomainEvent(DomainEvent):
            name = 'TestDomainEvent'

        class TestDomainSubscriber(DomainEventHandler):
            def process(x, event):
                nonlocal self
                self.listened_events_1.append(event)

            def listens_to(self):
                return [TestDomainEvent]

        class TestDomainSubscriber2(DomainEventHandler):
            def process(x, event):
                nonlocal self
                self.listened_events_2.append(event)

            def listens_to(self):
                return [TestDomainEvent]

        def thread_1_func():
            DomainEventBus.instance().reset()
            TestDomainSubscriber().listen()
            TestDomainEvent().emit()
            TestDomainEvent().emit()

        def thread_2_func():
            DomainEventBus.instance().reset()
            TestDomainSubscriber2().listen()
            TestDomainEvent().emit()
            TestDomainEvent().emit()
            TestDomainEvent().emit()

        t1 = Thread(target=thread_1_func)
        t2 = Thread(target=thread_2_func)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert len(self.listened_events_1) == 2
        assert len(self.listened_events_2) == 3

    def test_the_bus_will_not_allow_chained_event_publishing(self):
        self.listened_events_1 = []
        self.listened_events_2 = []

        class TestDomainEvent(DomainEvent):
            name = 'TestDomainEvent'

        class TestDomainEvent2(DomainEvent):
            name = 'TestDomainEvent2'

        class TestDomainSubscriber(DomainEventHandler):
            def process(x, event):
                nonlocal self
                self.listened_events_1.append(event)
                TestDomainEvent2().emit()

            def listens_to(self):
                return [TestDomainEvent]

        class TestDomainSubscriber2(DomainEventHandler):
            def process(x, event):
                nonlocal self
                self.listened_events_2.append(event)

            def listens_to(self):
                return [TestDomainEvent2]

        DomainEventBus.instance().reset()
        TestDomainSubscriber().listen()
        TestDomainSubscriber2().listen()
        TestDomainEvent().emit()

        assert len(self.listened_events_1) == 1
        assert len(self.listened_events_2) == 0

    def test_the_debugger_will_log_any_event(self):
        self.listened_events_1 = []
        self.listened_events_2 = []

        class TestDomainEvent(DomainEvent):
            name = 'TestDomainEvent'

        class TestDomainEvent2(DomainEvent):
            name = 'TestDomainEvent2'

        class TestDomainSubscriber(DomainEventHandler):
            def process(x, event):
                nonlocal self
                self.listened_events_1.append(event)
                TestDomainEvent2().emit()

            def listens_to(self):
                return [TestDomainEvent]

        class TestDomainSubscriber2(DomainEventHandler):
            def process(x, event):
                nonlocal self
                self.listened_events_2.append(event)

            def listens_to(self):
                return [TestDomainEvent2]

        DomainEventBus.instance().reset()
        TestDomainSubscriber().listen()
        TestDomainSubscriber2().listen()

        Debugger().listen()

        TestDomainEvent().emit()
