from typing import Any, List, Optional

from melange.backends.backend_manager import BackendManager
from melange.backends.interfaces import MessagingBackend
from melange.models import QueueWrapper, TopicWrapper


class MessagingBackendFactory:
    """
    Class used to create queues and topics
    """

    def __init__(self, backend: Optional[MessagingBackend] = None) -> None:
        self._backend = backend or BackendManager().get_default_backend()

    def init_queue(
        self,
        queue_name: str,
        topic_names_to_subscribe: Optional[List[str]] = None,
        dlq_name: Optional[str] = None,
        **kwargs: Any
    ) -> QueueWrapper:
        """
        Creates a queue if it does not exist, subscribes it to the topics, and creates a
        dead letter queue.

        Args:
            queue_name: name of the queue to create
            topic_names_to_subscribe: list of topic names to subscribe this queue. If
                the topics do not exist they will be created.
            dlq_name: name of the dead letter queue to create and attach to the main queue
            **kwargs: any other arguments required by your messaging backend

        Returns:
            The created queue wrapper

        """
        topic_names_to_subscribe = topic_names_to_subscribe or []
        topics = [self.init_topic(t) for t in topic_names_to_subscribe]

        queue, dlq = self._backend.declare_queue(
            queue_name, *topics, dead_letter_queue_name=dlq_name, **kwargs
        )

        return queue

    def init_topic(self, topic_name: str) -> TopicWrapper:
        """
        Creates a topic if it does not exist.
        Args:
            topic_name: the name of the topic to create

        Returns:
            The created topic wrapper

        """
        return self._backend.declare_topic(topic_name)
