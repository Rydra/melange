# type: ignore
"""
Looking for maintainers for the RabbitMQBackend!
"""


import json

import pika

from melange.backends.interfaces import MessagingBackend
from melange.models import Message


class RabbitMQBackend(MessagingBackend):
    def __init__(self, **kwargs):
        super().__init__()
        connection_parameters = pika.ConnectionParameters(**kwargs)
        self.connection = pika.BlockingConnection(connection_parameters)
        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=1)

    def retrieve_messages(self, queue):
        method_frame, properties, body = self.channel.basic_get(
            queue=queue, no_ack=False
        )

        if not method_frame:
            return []

        message = Message(
            message_id=str(method_frame.delivery_tag),
            content=json.loads(body.decode("utf-8")),
            metadata=properties,
        )
        return [message]

    def publish_to_topic(self, content, topic, event_type_name):
        result = self.channel.basic_publish(
            exchange=topic,
            routing_key="",
            body=content,
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ),
        )

        return result

    def get_queue(self, queue_name):
        queue = self.channel.queue_declare(queue=queue_name, durable=True)
        return queue.method.queue

    def declare_topic(self, topic_name):
        self.channel.exchange_declare(
            exchange=topic_name, exchange_type="fanout", durable=True
        )

        return topic_name

    def acknowledge(self, message):
        self.channel.basic_ack(delivery_tag=int(message.message_id))

    def declare_queue(self, queue_name, *topics_to_bind, dead_letter_queue_name=None):
        queue = self.channel.queue_declare(queue=queue_name, durable=True)
        if topics_to_bind:
            for topic in topics_to_bind:
                self.channel.queue_bind(exchange=topic, queue=queue_name)

        return queue.method.queue, dead_letter_queue_name

    def close_connection(self):
        self.connection.close()

    def delete_queue(self, queue):
        self.channel.queue_delete(queue=queue)

    def delete_topic(self, topic):
        self.channel.exchange_delete(exchange=topic)
