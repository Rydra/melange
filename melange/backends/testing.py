from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from melange.backends.interfaces import MessagingBackend
from melange.consumers import Consumer
from melange.message_dispatcher import MessageDispatcher
from melange.models import Message, QueueWrapper, TopicWrapper
from melange.serializers.registry import SerializerRegistry


def link_synchronously(
    queue_name: str,
    consumers: List[Consumer],
    serializer_registry: SerializerRegistry,
    backend: "InMemoryMessagingBackend",
) -> None:
    consumer_dispatcher = MessageDispatcher(serializer_registry, backend=backend)
    for consumer in consumers:
        consumer_dispatcher.attach_consumer(consumer)

    backend.set_callback(queue_name, consumer_dispatcher.consume_event)


class DumbObject:
    def __init__(self, name: str) -> None:
        self.name = name


class InMemoryMessagingBackend(MessagingBackend):
    def __init__(self) -> None:
        super().__init__()
        self._messages: List[Message] = []
        self.callbacks: Dict = {}

    def set_callback(self, queue_name: str, callback: Callable[[str], None]) -> None:
        self.callbacks[queue_name] = callback

    def declare_topic(self, topic_name: str) -> TopicWrapper:
        return TopicWrapper(DumbObject(topic_name))

    def get_queue(self, queue_name: str) -> QueueWrapper:
        return QueueWrapper(DumbObject(queue_name))

    def declare_queue(
        self,
        queue_name: str,
        *topics_to_bind: TopicWrapper,
        dead_letter_queue_name: Optional[str] = None,
        **kwargs: Any
    ) -> Tuple[QueueWrapper, Optional[QueueWrapper]]:
        return QueueWrapper(DumbObject(queue_name)), None

    def retrieve_messages(self, queue: QueueWrapper, **kwargs: Any) -> List[Message]:
        messages = self._messages
        self._messages = []
        return messages

    def yield_messages(self, queue: QueueWrapper, **kwargs: Any) -> Iterable[Message]:
        for message in self._messages:
            yield message

    def publish_to_topic(
        self,
        message: Message,
        topic: TopicWrapper,
        extra_attributes: Optional[Dict] = None,
    ) -> None:
        if topic.unwrapped_obj.name in self.callbacks:
            # Append the message internally to simulate "the queue",
            # then call the
            self._messages.append(message)

            self.callbacks[topic.unwrapped_obj.name](topic.unwrapped_obj.name)

    def publish_to_queue(
        self, message: Message, queue: QueueWrapper, **kwargs: Any
    ) -> None:
        if queue.unwrapped_obj.name in self.callbacks:
            # Append the message internally to simulate "the queue",
            # then call the
            self._messages.append(message)

            self.callbacks[queue.unwrapped_obj.name](queue.unwrapped_obj.name)

    def acknowledge(self, message: Message) -> None:
        return None

    def delete_queue(self, queue: QueueWrapper) -> None:
        return None

    def delete_topic(self, topic: TopicWrapper) -> None:
        return None
