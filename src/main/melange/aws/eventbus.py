from melange.aws.exchange_message_consumer import ThreadedExchangeMessageConsumer
from melange.aws.exchange_message_publisher import ExchangeMessagePublisher


class EventBus(ThreadedExchangeMessageConsumer, ExchangeMessagePublisher):
    _instance = None

    def __init__(self, event_queue_name, topic_to_subscribe):
        ThreadedExchangeMessageConsumer.__init__(self, event_queue_name, topic_to_subscribe)
        ExchangeMessagePublisher.__init__(self, topic_to_subscribe)

    @staticmethod
    def init(event_queue_name, topic_to_subscribe):
        EventBus._instance = EventBus(event_queue_name, topic_to_subscribe)

    @staticmethod
    def get_instance():
        if not EventBus._instance:
            raise Exception("The event bus has not been initialized. Call init first!")

        return EventBus._instance

    @staticmethod
    def set_instance(instance):
        """
        Only used for mocking purposes
        """
        EventBus._instance = instance
