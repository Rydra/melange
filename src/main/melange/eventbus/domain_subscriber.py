""" Subscriber super-class """
from melange.event import Event


class DomainSubscriber:

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
