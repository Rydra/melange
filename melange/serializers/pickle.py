import codecs
import pickle
from typing import Optional

from simple_cqrs.domain_event import DomainEvent

from melange.serializers.interfaces import MessageSerializer


class PickleSerializer(MessageSerializer[DomainEvent]):
    """
    Serializes DomainEvents with pickle
    """

    def manifest(self, data: DomainEvent) -> str:
        return data.__class__.__qualname__

    def deserialize(self, data: str, manifest: Optional[str] = None) -> DomainEvent:
        return pickle.loads(codecs.decode(data.encode(), "base64"))

    def serialize(self, data: DomainEvent) -> str:
        return codecs.encode(pickle.dumps(data), "base64").decode()
