from melange.infrastructure.singleton import Singleton


@Singleton
class EventSerializer:
    def __init__(self):
        self.event_serializer_map = {}

    def register(self, *serializers):
        for serializer in serializers:
            self.event_serializer_map[serializer.__qualname__] = serializer()

    def deserialize(self, event_dict):
        event_schema = event_dict['event_type_name'] + 'Schema'

        if event_schema not in self.event_serializer_map:
            raise ValueError("The event type {} doesn't have a registered serializer".format(event_dict['event_type_name']))

        schema = self.event_serializer_map[event_schema]
        data, errors = schema.load(event_dict)
        return data

    def serialize(self, event):
        event_schema = event.event_type_name + 'Schema'

        if event_schema not in self.event_serializer_map:
            raise ValueError("The event type {} doesn't have a registered serializer".format(event.event_type_name))

        schema = self.event_serializer_map[event_schema]
        data, errors = schema.dumps(event)
        return data
