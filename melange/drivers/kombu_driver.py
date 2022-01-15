from typing import Any, Dict, Generic, List, Optional, Protocol, Tuple, TypeVar

from kombu import Connection, Exchange
from kombu import Queue as KQueue

from melange.drivers.interfaces import Message, MessagingDriver, Queue, Topic

T = TypeVar("T")
Q = TypeVar("Q")


class KombuDriver(MessagingDriver):
    def __init__(self, connection: str, **kwargs) -> None:
        super().__init__()
        self.connection = connection
        self.wait_time_seconds = kwargs.get("wait_time_seconds", 10)

    def declare_queue(
        self,
        queue_name: str,
        *topics_to_bind: Exchange,
        dead_letter_queue_name: str = None,
        **kwargs
    ) -> Tuple[Queue, Optional[Queue]]:
        queue = KQueue(queue_name, bindings=topics_to_bind, routing_key=queue_name)
        with Connection(self.connection) as conn:
            queue(conn).declare()
        return queue, None

    def get_queue(self, queue_name: str) -> Queue:
        return self.declare_queue(queue_name)[0]

    def declare_topic(self, topic_name: str) -> Topic:
        media_exchange = Exchange(topic_name, "fanout", durable=True)
        with Connection(self.connection) as conn:
            media_exchange(conn).declare()
        return media_exchange

    def retrieve_messages(self, queue: Queue, attempt_id=None) -> List[Message]:
        messages = []

        def process_media(body, message):
            messages.append(_construct_message(body, message))

        with Connection(self.connection) as conn:
            with conn.Consumer(queue, callbacks=[process_media]):
                # Process messages and handle events on all channels
                conn.drain_events(timeout=self.wait_time_seconds)

        return messages

    def acknowledge(self, message: Message) -> None:
        message.metadata.ack()

    def delete_queue(self, queue: KQueue) -> None:
        """
        Deletes the queue
        """
        with Connection(self.connection) as conn:
            queue(conn).delete()

    def delete_topic(self, topic: Exchange) -> None:
        """
        Deletes the topic
        """
        with Connection(self.connection) as conn:
            topic(conn).delete()

    def publish(
        self,
        content: str,
        topic: Topic,
        event_type_name: str,
        extra_attributes: Dict = None,
    ):
        """
        Publishes the content to the topic. The content must be a
        string (which is the json representation of an event)
        """
        with Connection(self.connection) as conn:
            producer = conn.Producer(serializer="json")
            producer.publish({"Message": content}, exchange=topic, routing_key="*")

    def queue_publish(
        self,
        content: str,
        queue: Queue,
        event_type_name: str = None,
        message_group_id: str = None,
        message_deduplication_id: str = None,
    ):
        with Connection(self.connection) as conn:
            producer = conn.Producer(serializer="json")
            producer.publish(
                {"message": content, "manifest": event_type_name},
                exchange="",
                routing_key=queue.name,
            )


def _construct_message(body: Any, message) -> Message:
    message_content = body["message"]
    manifest = body["manifest"]

    return Message(message.message_id, message_content, message, manifest)
