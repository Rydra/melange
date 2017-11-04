""" Subscriber super-class """
from melange.aws.cache import Cache
from melange.aws.utils import get_fully_qualified_name
from melange.event import Event


class DomainEventSubscriber:

    def process(self, event):
        """
        Called by the eventbus.

        :param event: The event object
        :type event: Event or subclass of event

        This method implements the logic for processing the event. This method should not block for
        long time as that will affect the performance of the eventbus.
        """
        pass

    def listens_to(self):
        return []

    def accepts(self, event):
        return isinstance(event, Event) \
               and self.listens_to() == [] or type(event) in self.listens_to()


class ExchangeListener:
    def __init__(self, topic):
        self.topic = topic

    def process_event(self, event, **kwargs):
        if get_fully_qualified_name(self) + '.' + kwargs['message_id'] in Cache.instance():
            print('detected a duplicated message, ignoring')
            return

        self.process(event, **kwargs)

        Cache.instance().store(get_fully_qualified_name(self) + '.' + kwargs['message_id'], get_fully_qualified_name(self) + '.' + kwargs['message_id'])

    def process(self, event, **kwargs):
        """
        Called by the eventbus.

        :param event: The event object
        :type event: Event or subclass of event

        This method implements the logic for processing the event. This method should not block for
        long time as that will affect the performance of the eventbus.
        """
        pass

    def get_topic(self):
        return self.topic

    def listens_to(self):
        return None

    def accepts(self, event):
        return isinstance(event, Event) \
               and (self.listens_to() == Event.ALL or self.listens_to() == event.event_type_name)
