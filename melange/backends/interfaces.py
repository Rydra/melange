import weakref
from typing import Any, Dict, Iterable, List, Optional, Tuple

from melange.models import Message, QueueWrapper, TopicWrapper


class MessagingBackend:
    def __init__(self) -> None:
        self._finalizer = weakref.finalize(self, self.close_connection)

    def declare_topic(self, topic_name: str) -> TopicWrapper:
        """
        Gets or creates a topic.

        Args:
            topic_name: The name of the topic to create

        Returns:
            An object that represents a topic. The type of the object
            is only relevant inside the context of the backend, so what you
            return as a topic will be passed in next calls to the backend
            where a topic is required
        """
        raise NotImplementedError

    def get_queue(self, queue_name: str) -> QueueWrapper:
        """
        Gets the queue with the name `queue_name`. Does not perform creation.

        Args:
            queue_name: the name of the queue to retrieve

        Returns:
            A `Queue` object that represents the created the queue
        """
        raise NotImplementedError

    def declare_queue(
        self,
        queue_name: str,
        *topics_to_bind: TopicWrapper,
        dead_letter_queue_name: Optional[str] = None,
        **kwargs: Any
    ) -> Tuple[QueueWrapper, Optional[QueueWrapper]]:
        """
        Gets or creates a queue.

        Args:
            queue_name: the name of the queue to create
            *topics_to_bind: if provided, creates all these topics and subscribes
                the created queue to them
            dead_letter_queue_name: if provided, create a dead letter queue attached to
                the created `queue_name`.
            **kwargs:

        Returns:
            A tuple with the created queue and the dead letter queue (if applies)
        """

        raise NotImplementedError

    def retrieve_messages(self, queue: QueueWrapper, **kwargs: Any) -> List[Message]:
        """
        Retrieves a list of available messages from the queue.

        Args:
            queue: the queue object
            **kwargs: Other parameters/options required by the backend

        Returns:
            A list of available messages from the queue
        """
        raise NotImplementedError

    def yield_messages(self, queue: QueueWrapper, **kwargs: Any) -> Iterable[Message]:
        """
        Yields available messages from the queue.

        Args:
            queue: the queue object
            **kwargs: Other parameters/options required by the backend

        Returns:
            An iterable which will poll the queue upon requesting more messages
        """
        raise NotImplementedError

    def publish_to_topic(
        self,
        message: Message,
        topic: TopicWrapper,
        extra_attributes: Optional[Dict] = None,
    ) -> None:
        """
        Publishes a message content and the manifest to the topic

        Args:
            message: the message to send
            topic: the topic to send the message to
            extra_attributes: extra properties that might be required for the backend
        """
        raise NotImplementedError

    def publish_to_queue(
        self, message: Message, queue: QueueWrapper, **kwargs: Any
    ) -> None:
        raise NotImplementedError

    def acknowledge(self, message: Message) -> None:
        """
        Acknowledges a message so that it won't be redelivered by
        the messaging infrastructure in the future
        """
        raise NotImplementedError

    def close_connection(self) -> None:
        """
        Override this function if you want to use some finalizer code
         to shutdown your backend in a clean way
        """
        pass

    def delete_queue(self, queue: QueueWrapper) -> None:
        """
        Deletes the queue
        """
        raise NotImplementedError

    def delete_topic(self, topic: TopicWrapper) -> None:
        """
        Deletes the topic
        """
        raise NotImplementedError
