from melange.aws.cache import Cache
from melange.aws.utils import get_fully_qualified_name
from melange.event import Event


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
        # None = listens to every event
        return None

    def accepts(self, event_type_name):
        return not self.listens_to() or event_type_name in self.listens_to()
