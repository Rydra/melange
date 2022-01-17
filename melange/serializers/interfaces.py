from typing import Generic, Optional

from melange.helpers.typing import T


class MessageSerializer(Generic[T]):
    """
    You need to provide a way to convert a message from your sqs
    into something meaningful for your domain (e.g. into a Domain Event)
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
