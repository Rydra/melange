import json
import logging

from redis_cache import SimpleCache

from melange import settings
from melange.event import Event

from melange.aws.event_serializer import EventSerializer
from melange.aws.messaging_manager import MessagingManager
from melange.exchangelistener import ExchangeListener


class ExchangeMessageConsumer:
    def __init__(self, event_queue_name, topic_to_subscribe, host=None, port=None, db=None, password=None):
        self.consumers = {}
        topic = MessagingManager.declare_topic(topic_to_subscribe)
        self.event_queue, _ = MessagingManager.declare_queue(event_queue_name, topic)

        # The redis cache is used to provide message deduplication
        self.cache = SimpleCache(expire=3600,
                                 host=host or settings.REDIS_HOST,
                                 port=port or settings.REDIS_PORT,
                                 db=db or settings.REDIS_DB,
                                 password=password or settings.REDIS_PASSWORD)

        self._message_processor = self._process_message_with_deduplication
        if not self.cache.connection:
            logging.warning("Could not establish a connection with redis. Message deduplication won't work")
            self._message_processor = self._process_message

    def subscribe(self, consumer):

        if not isinstance(consumer, ExchangeListener):
            return False

        listened_event_type_name = consumer.listens_to()

        if listened_event_type_name not in self.consumers:
            self.consumers[listened_event_type_name] = []

        self.consumers[listened_event_type_name].append(consumer)

        return True

    def unsubscribe(self, consumer):

        listened_event_type_name = consumer.listens_to()

        if listened_event_type_name in self.consumers and consumer in self.consumers[listened_event_type_name]:
            self.consumers[listened_event_type_name].remove(consumer)

            if len(self.consumers[listened_event_type_name]) == 0:
                del self.consumers[listened_event_type_name]

    def consume_event(self):
        self._poll_next_event()

    def _get_subscribers(self, event_type_name):
        return self.consumers[event_type_name] if event_type_name in self.consumers else []

    def _poll_next_event(self):

        messages = self.event_queue.receive_messages(MaxNumberOfMessages=1, VisibilityTimeout=100,
                                                     WaitTimeSeconds=10, AttributeNames=['All'])

        for message in messages:
            try:
                self._message_processor(message)
            except Exception as e:
                logging.error(e)

    def _process_message_with_deduplication(self, message, **kwargs):
        if message.message_id in self.cache:
            print('detected a duplicated message, ignoring')
            message.delete()
            return

        self._process_message(message)

        self.cache.store(message.message_id, message.message_id)
        message.delete()

    def _process_message(self, message, **kwargs):

        body = message.body
        message_content = json.loads(body)
        if 'Message' in message_content:
            content = json.loads(message_content['Message'])
        else:
            content = message_content

        if 'event_type_name' not in content:
            return

        try:
            event = EventSerializer.instance().deserialize(content)
        except ValueError:
            event = json.loads(content)

        event_type_name = event.event_type_name if isinstance(event, Event) else event['event_type_name']
        for subscr in self._get_subscribers(event_type_name):
            try:
                subscr.process(event, **kwargs)
            except Exception as e:
                logging.error(e)

        message.delete()
