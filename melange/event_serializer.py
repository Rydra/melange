import json
from typing import Generic, Dict, Optional

from melange.helpers.typing import T


class MessageSerializer(Generic[T]):
    """
    You need to provide a way to convert a message from your sqs
    into something meaningful for your domain (e.g. into a Domain Event)
    """

    def manifest(self, data: T) -> str:
        return ""

    def deserialize(self, data: str, manifest: Optional[str] = None) -> str:
        pass

    def serialize(self, data: T) -> str:
        """
        Serializes and object to a string representation
        """
        pass


class JsonSQSSerializer(MessageSerializer[Dict]):
    def manifest(self, data: Dict):
        return "json"

    def deserialize(self, serialized_data: str, manifest: Optional[str] = None) -> str:
        data = json.loads(serialized_data)
        return data

    def serialize(self, data: Dict) -> str:
        return json.dumps(data)
