import json
from typing import Dict, Optional

from bunch import Bunch

from melange.exceptions import SerializationError
from melange.helpers.typing import T
from melange.serializers.interfaces import Serializer


class MyOwnSerializer(Serializer):
    # If you define a constructor for you serializer, it should accept no parameters

    @staticmethod
    def identifier() -> int:
        """
        Pick a unique identifier for your Serializer.
        The numbers 0 to 40 are reserved for Melange itself
        """
        return 123

    def manifest(self, data: T) -> Optional[str]:
        """
        The manifest is a type hint used on deserialization
        """
        if isinstance(data, Bunch):
            return "bunch"
        if isinstance(data, Dict):
            return "dictionary"
        else:
            raise SerializationError(
                "The data object cannot be used with this serializer"
            )

    def deserialize(self, data: str, manifest: Optional[str] = None) -> T:
        """
        `deserialize` uses the manifest as a type hint
        """
        if manifest == "dictionary":
            deserialized_data = json.loads(data)
            return deserialized_data
        elif manifest == "bunch":
            deserialized_data = Bunch(json.loads(data))
            return deserialized_data
        else:
            raise SerializationError("Unknown manifest")

    def serialize(self, data: T) -> str:
        """
        Serializes the given object to an string
        """
        if isinstance(data, Bunch):
            return json.dumps(dict(data))
        elif isinstance(data, Dict):
            return json.dumps(data)
        else:
            raise SerializationError("This type cannot be used with this serializer")
