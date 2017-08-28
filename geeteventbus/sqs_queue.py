import json

import boto3
import jsonpickle

from geeteventbus.settings import Settings


class SQSQueue:

    def __init__(self):
        sqs = boto3.resource('sqs')
        self.queue = sqs.get_queue_by_name(QueueName=Settings.SQS_QUEUE_NAME)

        self.sns = boto3.client('sns')
        self.last_message = None

        self.registered_event_types = {}

    def register_event_type(self, event_type):
        self.registered_event_types[event_type.get_event_type_name()] = event_type

    def put(self, eventobj):
        message = jsonpickle.encode(eventobj, unpicklable=False)

        self.sns.publish(
            TopicArn=Settings.SNS_TOPIC_ARN,
            Message=message
        )

    def get(self, timeout=0):

        gathered_message = None
        for message in self.queue.receive_messages():
            gathered_message = message
            message.delete()

        if gathered_message is None:
            return None

        data = jsonpickle.decode(gathered_message.body)

        if data['event_type_name'] not in self.registered_event_types:
            return None

        return self.registered_event_types[data['event_type_name']](**data)

    def task_done(self):
        if self.last_message:
            self.last_message.delete()
