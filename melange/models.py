from typing import Any, Optional


class TopicWrapper:
    """
    Wrapper class for a topic of any infrastructure technology.
    It's intended to only be unwrapped at the messaging backend
    who is the only one responsible to handle the specifics
    """

    def __init__(self, obj: Any) -> None:
        self.obj = obj

    @property
    def unwrapped_obj(self) -> Any:
        return self.obj

    def unwrap(self) -> Any:
        return self.obj


class QueueWrapper:
    """
    Wrapper class for a queue of any infrastructure technology
    """

    def __init__(self, obj: Any) -> None:
        self.obj = obj

    @property
    def unwrapped_obj(self) -> Any:
        return self.obj

    def unwrap(self) -> Any:
        return self.obj


class Message:
    def __init__(
        self,
        message_id: Optional[str],
        content: str,
        metadata: Any,
        serializer_id: Optional[int],
        manifest: Optional[str] = None,
    ) -> None:
        self.message_id = message_id
        self.content = content
        self.metadata = metadata
        self.serializer_id = serializer_id
        self.manifest = manifest

    @staticmethod
    def create(
        content: str, manifest: Optional[str], serializer_id: int, metadata: Any = None
    ) -> "Message":
        return Message(None, content, metadata, serializer_id, manifest)

    def get_message_manifest(self) -> Optional[str]:
        return self.manifest
