""" Subscriber super-class """


class Subscriber:
    def __init__(self):
        pass

    def process(self, eventobj):
        """
        Called by the eventbus.

        :param eventobj: The event object
        :type eventobj: Event or subclass of event

        This method implements the logic for processing the event. This method should not block for
        long time as that will affect the performance of the eventbus.
        """
        pass

    def listens_to(self):
        return None
