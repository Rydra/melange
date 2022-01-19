from typing import Generic, Optional

from melange.helpers.typing import T


class MessageSerializer(Generic[T]):
    """
    Base interface to inherit for all the serializers of the platform
    """

    def manifest(self, data: T) -> str:
        return ""

    def deserialize(self, data: str, manifest: Optional[str] = None) -> T:
        pass

    def serialize(self, data: T) -> str:
        """
        Serializes and object to a string representation
        """
        pass
