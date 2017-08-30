from geeteventbus.aws.message_consumer import MessageConsumer
from geeteventbus.aws.message_publisher import MessagePublisher


class SQSEventBus(MessageConsumer, MessagePublisher):
    _instance = None

    def __init__(self, event_serializer, event_queue_name, topic_to_subscribe):
        MessageConsumer.__init__(self, event_serializer, event_queue_name, topic_to_subscribe)
        MessagePublisher.__init__(self, event_serializer)

    @staticmethod
    def init(event_serializer_map, event_queue_name, topic_to_subscribe):
        SQSEventBus._instance = SQSEventBus(event_serializer_map, event_queue_name, topic_to_subscribe)

    @staticmethod
    def get_instance():
        if not SQSEventBus._instance:
            raise Exception("The event bus has not been initialized. Call init first!")

        return SQSEventBus._instance

    @staticmethod
    def set_instance(instance):
        """
        Only used for mocking purposes
        """
        SQSEventBus._instance = instance
