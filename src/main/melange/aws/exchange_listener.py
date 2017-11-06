from melange.aws.cache import Cache
from melange.aws.eventmessage import EventMessage
from melange.aws.utils import get_fully_qualified_name


class ExchangeListener:
    def process_event(self, event, **kwargs):
        if get_fully_qualified_name(self) + '.' + kwargs['message_id'] in Cache.instance():
            print('detected a duplicated message, ignoring')
            return

        self.process(event, **kwargs)

        Cache.instance().store(get_fully_qualified_name(self) + '.' + kwargs['message_id'], get_fully_qualified_name(self) + '.' + kwargs['message_id'])

    def process(self, event, **kwargs):
        """
        Called by the domain_event_bus.

        :param event: The event object
        :type event: EventMessage or subclass of event

        This method implements the logic for processing the event. This method should not block for
        long time as that will affect the performance of the domain_event_bus.
        """
        pass

    def listens_to(self):
        # None = listens to every event
        return None

    def accepts(self, event_type_name):
        return not self.listens_to() or event_type_name in self.listens_to()
