from melange.infrastructure.singleton import Singleton


@Singleton
class EventSerializer:
    def __init__(self):
        self.event_serializer_map = {}

    def initialize(self, event_serializer_map):
        self.event_serializer_map = event_serializer_map

    def deserialize(self, event_dict):
        event_type_name = event_dict['event_type_name']

        if event_type_name not in self.event_serializer_map:
            raise ValueError("The event type {} doesn't have a registered serializer")

        schema = self.event_serializer_map[event_type_name]
        return schema.load(event_dict).data

    def serialize(self, event):

        event_type_name = event.event_type_name

        if event_type_name not in self.event_serializer_map:
            raise ValueError("The event type {} doesn't have a registered serializer")

        schema = self.event_serializer_map[event_type_name]
        return schema.dumps(event).data
