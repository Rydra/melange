from typing import List
from uuid import uuid4

from melange.backends.interfaces import Message, MessagingBackend
from melange.consumers import Consumer
from melange.message_dispatcher import ConsumerDispatcher
from melange.serializers.interfaces import MessageSerializer


def link_synchronously(
    queue_name: str,
    consumers: List[Consumer],
    serializer: MessageSerializer,
    backend: "InMemoryMessagingBackend",
) -> None:
    consumer_dispatcher = ConsumerDispatcher(serializer, backend=backend)
    for consumer in consumers:
        consumer_dispatcher.subscribe(consumer)

    backend.set_callback(queue_name, consumer_dispatcher.consume_event)


class DumbQueue:
    def __init__(self, name):
        self.name = name
        self.attributes = {}


class InMemoryMessagingBackend(MessagingBackend):
    def __init__(self):
        super().__init__()
        self._messages = []
        self.callbacks = {}

    def set_callback(self, queue_name, callback):
        self.callbacks[queue_name] = callback

    def declare_topic(self, topic_name):
        return None

    def get_queue(self, queue_name):
        return DumbQueue(queue_name)

    def declare_queue(
        self, queue_name, *topics_to_bind, dead_letter_queue_name=None, **kwargs
    ):
        return DumbQueue(queue_name), None

    def retrieve_messages(self, queue, attempt_id=None):
        messages = self._messages
        self._messages = []
        return messages

    def publish(self, content, topic, event_type_name, extra_attributes=None):
        if topic.name in self.callbacks:
            message = Message(str(uuid4()), content, None, manifest=event_type_name)
            # Append the message internally to simulate "the queue",
            # then call the
            self._messages.append(message)

            self.callbacks[topic.name](topic.name)

    def queue_publish(
        self,
        content,
        queue,
        event_type_name,
        message_group_id=None,
        message_deduplication_id=None,
    ):
        self.publish(content, queue, event_type_name)

    def acknowledge(self, message):
        return None

    def delete_queue(self, queue):
        return None

    def delete_topic(self, topic):
        return None
