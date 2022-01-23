from simple_cqrs.domain_event import DomainEvent

from melange.serializers import PickleSerializer, SerializerRegistry

serializer_settings = {
    "serializers": {"pickle": PickleSerializer},
    "serializer_bindings": {DomainEvent: "pickle"},
}

serializer_registry = SerializerRegistry(serializer_settings)
