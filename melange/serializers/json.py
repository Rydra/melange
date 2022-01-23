import json
from typing import Dict, Optional

from melange.serializers.interfaces import Serializer


class JsonSerializer(Serializer[Dict]):
    """
    Serializes and deserializes python dictionaries in json format
    """

    @staticmethod
    def identifier() -> int:
        return 1

    def manifest(self, data: Dict) -> str:
        return "json"

    def deserialize(self, serialized_data: str, manifest: Optional[str] = None) -> Dict:
        data = json.loads(serialized_data)
        return data

    def serialize(self, data: Dict) -> str:
        return json.dumps(data)
