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

    def put(self, eventobj):
        self.sns.publish(
            TopicArn=Settings.SNS_TOPIC_ARN,
            Message=jsonpickle.encode(eventobj, unpicklable=False)
        )

    def get(self, timeout=0):

        for message in self.queue.receive_messages():
            self.last_message = message

            return json.loads(message.body)

    def task_done(self):
        if self.last_message:
            self.last_message.delete()
