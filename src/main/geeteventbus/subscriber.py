''' Subscriber super-class '''

import logging
from threading import current_thread
from geeteventbus.event import Event

class Subscriber:

    def __init__(self):
        pass

    def process(self, eventobj):
        '''
        Called by the eventbus.

        :param eventobj: The event object
        :type eventobj: Event or subclass of event

        This method implements the logic for processing the event. This method should not block for
        long time as that will affect the performance of the eventbus.
        '''
        if not self.registered:
            logging.error('Subscriber is not registered')
            return
        if not isinstance(eventobj, Event):
            logging.error('Invalid object type is passed.')
            return
        print('%s %s %s %s' % (current_thread().getName(), 'processing', eventobj.get_topic(),
               str(eventobj.get_data())))

    def listens_to(self):
        return None