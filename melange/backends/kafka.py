from typing import Any, Dict, Iterable, List, Optional, Tuple

from melange.backends.interfaces import MessagingBackend
from melange.models import Message, QueueWrapper, TopicWrapper


class KafkaBackend(MessagingBackend):
    """
    Kafka works differently than, say, SQS. You connect with the Kafka consumer
    to a list of topics, and then you iterate over them to obtain the messages
    """

    def declare_topic(self, topic_name: str) -> TopicWrapper:
        pass

    def get_queue(self, queue_name: str) -> QueueWrapper:
        pass

    def declare_queue(
        self,
        queue_name: str,
        *topics_to_bind: TopicWrapper,
        dead_letter_queue_name: Optional[str] = None,
        **kwargs: Any
    ) -> Tuple[QueueWrapper, Optional[QueueWrapper]]:
        pass

    def retrieve_messages(self, queue: QueueWrapper, **kwargs: Any) -> List[Message]:
        pass

    def yield_messages(self, queue: QueueWrapper, **kwargs: Any) -> Iterable[Message]:
        pass

    def publish_to_topic(
        self,
        message: Message,
        topic: TopicWrapper,
        extra_attributes: Optional[Dict] = None,
    ) -> None:
        pass

    def publish_to_queue(
        self, message: Message, queue: QueueWrapper, **kwargs: Any
    ) -> None:
        pass

    def acknowledge(self, message: Message) -> None:
        pass

    def close_connection(self) -> None:
        super().close_connection()

    def delete_queue(self, queue: QueueWrapper) -> None:
        pass

    def delete_topic(self, topic: TopicWrapper) -> None:
        pass

    def __init__(self, config: Dict) -> None:
        super().__init__()
        self.config = config
