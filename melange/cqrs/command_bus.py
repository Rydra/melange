from funcy import lfilter

from singleton import Singleton

from melange.cqrs.handlers import CommandHandler


class CommandBus(metaclass=Singleton):
    # TODO: For now let's make the command bus synchronous. In the future
    # we should make this async, as it is more conventional for regular
    # CQRS architectures
    def __init__(self):
        self.handlers = {}

    def register_handler(self, handler: CommandHandler):
        handled_commands = lfilter(lambda t: t is not object, handler.execute.registry)
        for handled_command in handled_commands:
            self.handlers[handled_command] = handler

    def reset(self):
        self.handlers.clear()

    def send(self, command):
        handler = self.handlers.get(type(command))
        if handler:
            return handler.execute(command)
