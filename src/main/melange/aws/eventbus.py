from melange.aws.threaded_message_consumer import ThreadedMessageConsumer
from melange.aws.message_publisher import MessagePublisher


class EventBus(ThreadedMessageConsumer, MessagePublisher):
    _instance = None

    def __init__(self, event_queue_name, topic_to_subscribe):
        ThreadedMessageConsumer.__init__(self, event_queue_name, topic_to_subscribe)
        MessagePublisher.__init__(self, topic_to_subscribe)

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
