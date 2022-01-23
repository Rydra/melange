import codecs
import pickle
from typing import Optional

from simple_cqrs.domain_event import DomainEvent

from melange.serializers.interfaces import Serializer


class PickleSerializer(Serializer[DomainEvent]):
    """
    Serializes DomainEvents with pickle.
    """

    @staticmethod
    def identifier() -> int:
        return 2

    def manifest(self, data: DomainEvent) -> str:
        return data.__class__.__qualname__

    def deserialize(self, data: str, manifest: Optional[str] = None) -> DomainEvent:
        return pickle.loads(codecs.decode(data.encode(), "base64"))

    def serialize(self, data: DomainEvent) -> str:
        return codecs.encode(pickle.dumps(data), "base64").decode()
