from methoddispatch import SingleDispatch, singledispatch

from melange.messaging import ExchangeListener


class CommandHandler(SingleDispatch):
    @singledispatch
    def execute(self, command):
        pass


command_handler = CommandHandler.execute.register


class QueryHandler(SingleDispatch):
    @singledispatch
    def execute(self, command):
        pass


query_handler = QueryHandler.execute.register


class Command:
    pass


class Query:
    pass


class AsyncReadModel(ExchangeListener):
    pass


class WorkflowHandler(ExchangeListener):
    pass
