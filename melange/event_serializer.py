import json
from typing import Generic, Tuple, Dict

from melange.helpers.typing import T


class MessageSerializer(Generic[T]):
    """
    You need to provide a way to convert a message from your sqs
    into something meaningful for your domain (e.g. into a Domain Event)
    """

    def deserialize(self, data: any) -> Tuple[T, str]:
        pass

    def serialize(self, serialized_data: T, manifest=None) -> str:
        """
        Serializes and object to a string representation
        """
        pass


class DefaultEventSerializer(MessageSerializer):
    def deserialize(self, serialized_data: str) -> Tuple[Dict, str]:
        data = json.loads(serialized_data)
        return data, data.get("manifest")

    def serialize(self, serialized_data: Dict, manifest=None) -> str:
        serialized_data["manifest"] = manifest
        return json.dumps(serialized_data)
