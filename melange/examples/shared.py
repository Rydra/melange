from simple_cqrs.domain_event import DomainEvent

from melange.serializers.pickle import PickleSerializer
from melange.serializers.registry import SerializerRegistry

serializer_settings = {
    "serializers": {"pickle": PickleSerializer},
    "serializer_bindings": {DomainEvent: "pickle"},
}

serializer_registry = SerializerRegistry(serializer_settings)
