from melange.domain_event_bus import DomainEvent


class DomainEventSerializer:
    def serialize(self, event: DomainEvent) -> str:
        raise NotImplementedError

    def deserialize(self, serialized_event: str, manifest) -> DomainEvent:
        pass


class DedupCache:
    def store(self, key, value, expire=None):
        raise NotImplementedError

    def get(self, key):
        raise NotImplementedError
