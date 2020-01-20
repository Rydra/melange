import uuid

from methoddispatch import SingleDispatch, singledispatch

from melange.cqrs.eventsourcing import EventStream


class AggregateRoot:
    pass


class AggregateId:
    @staticmethod
    def generate():
        return str(uuid.uuid4())


class EventSourcedAggregateRoot(AggregateRoot, SingleDispatch):
    def __init__(self, event_stream: EventStream):
        self._changes = []
        self.version = event_stream.version
        for event in event_stream.events:
            self.mutate(event)

    def add_event(self, event):
        self._changes.append(event)

    @singledispatch
    def mutate(self, event):
        pass

    def _apply(self, event):
        self.mutate(event)
        self.add_event(event)


mutator = EventSourcedAggregateRoot.mutate.register
