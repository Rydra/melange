from uuid import uuid4

from melange.drivers.interfaces import MessagingDriver, Message


class DumbQueue:
    def __init__(self, name):
        self.name = name
        self.attributes = {}


class InMemoryMessagingDriver(MessagingDriver):
    def __init__(self, callback=None, only_queues=None):
        super().__init__()
        self._messages = []
        self.callback = callback
        self._only_queues = only_queues or []

    def set_callback(self, callback):
        self.callback = callback

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
        if not self._only_queues or topic.name in self._only_queues:
            message = Message(str(uuid4()), content, None, manifest=event_type_name)
            self._messages.append(message)

            if self.callback:
                self.callback(message)

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
