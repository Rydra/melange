from typing import Any, Optional

from melange.backends.backend_manager import BackendManager
from melange.backends.interfaces import MessagingBackend, Topic


class MessagingBackendFactory:
    def __init__(self, backend: Optional[MessagingBackend] = None) -> None:
        self._backend = backend or BackendManager().get_backend()

    def init_queue(
        self,
        queue_name: str,
        *topic_names_to_subscribe: str,
        dlq_name: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        topics = [self.init_topic(t) for t in topic_names_to_subscribe]

        self._backend.declare_queue(
            queue_name,
            *topics,
            dead_letter_queue_name=dlq_name,
            filter_events=kwargs.get("filter_events")
        )

    def init_topic(self, topic_name: str) -> Topic:
        return self._backend.declare_topic(topic_name)
