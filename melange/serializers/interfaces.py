from abc import ABC, abstractmethod
from typing import Generic, Optional

from melange.helpers.typing import T


class Serializer(ABC, Generic[T]):
    """
    Base interface to inherit for all the serializers
    """

    @staticmethod
    @abstractmethod
    def identifier() -> int:
        raise NotImplementedError

    def manifest(self, data: T) -> Optional[str]:
        """
        Given an object which represents some data, return the
        manifest of that object (if any)
        Args:
            data:

        Returns:
            The manifest of the object
        """
        return None

    def deserialize(self, data: str, manifest: Optional[str] = None) -> T:
        """
        Deserializes a data string. The manifest helps the serializer by
        providing information on how this object must be deserialized.
        Args:
            data: the data string to deserialize
            manifest: the manifest that corresponds to the serialized string

        Returns:
            The data object
        """
        pass

    def serialize(self, data: T) -> str:
        """
        Serializes and object to a string representation
        Args:
            data: the data object to serialize

        Returns:
            A string representation of the `data` object made with this serializer
        """
        pass
