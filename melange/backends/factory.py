from typing import Any, List, Optional

from melange.backends.backend_manager import BackendManager
from melange.backends.interfaces import MessagingBackend
from melange.models import QueueWrapper, TopicWrapper


class MessagingBackendFactory:
    def __init__(self, backend: Optional[MessagingBackend] = None) -> None:
        self._backend = backend or BackendManager().get_default_backend()

    def init_queue(
        self,
        queue_name: str,
        topic_names_to_subscribe: Optional[List[str]] = None,
        dlq_name: Optional[str] = None,
        **kwargs: Any
    ) -> QueueWrapper:
        topic_names_to_subscribe = topic_names_to_subscribe or []
        topics = [self.init_topic(t) for t in topic_names_to_subscribe]

        queue, dlq = self._backend.declare_queue(
            queue_name,
            *topics,
            dead_letter_queue_name=dlq_name,
            filter_events=kwargs.get("filter_events")
        )

        return queue

    def init_topic(self, topic_name: str) -> TopicWrapper:
        return self._backend.declare_topic(topic_name)
