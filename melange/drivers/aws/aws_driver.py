import json
import uuid
from json import JSONDecodeError
from typing import Tuple, Dict, List

import boto3

from melange.drivers.interfaces import Queue, Topic, MessagingDriver, Message


class AWSDriver(MessagingDriver):
    def __init__(self, **kwargs):
        super().__init__()
        self.max_number_of_messages = kwargs.get("max_number_of_messages", 10)
        self.visibility_timeout = kwargs.get("visibility_timeout", 100)
        self.wait_time_seconds = kwargs.get("wait_time_seconds", 10)

    def declare_topic(self, topic_name) -> Topic:
        sns = boto3.resource("sns")
        topic = sns.create_topic(Name=topic_name)
        return topic

    def get_queue(self, queue_name) -> Queue:
        sqs_res = boto3.resource("sqs")

        return sqs_res.get_queue_by_name(QueueName=queue_name)

    def declare_queue(
        self,
        queue_name: str,
        *topics_to_bind: Topic,
        dead_letter_queue_name: str = None,
        **kwargs
    ) -> Tuple[Queue, Queue]:
        try:
            queue = self.get_queue(queue_name)
        except Exception:
            queue = self._create_queue(queue_name, content_based_deduplication="true")

        if topics_to_bind:
            statements = []
            for topic in topics_to_bind:
                statement = {
                    "Sid": "Sid{}".format(uuid.uuid4()),
                    "Effect": "Allow",
                    "Principal": "*",
                    "Resource": queue.attributes["QueueArn"],
                    "Action": "sqs:SendMessage",
                    "Condition": {"ArnEquals": {"aws:SourceArn": topic.arn}},
                }

                statements.append(statement)
                subscription = topic.subscribe(
                    Protocol="sqs",
                    Endpoint=queue.attributes[
                        "QueueArn"
                    ],  # , Attributes={"RawMessageDelivery": "true"}
                )

                if kwargs.get("filter_events"):
                    filter_policy = {"event_type": kwargs["filter_events"]}
                else:
                    filter_policy = {}

                subscription.set_attributes(
                    AttributeName="FilterPolicy",
                    AttributeValue=json.dumps(filter_policy),
                )

            policy = {
                "Version": "2012-10-17",
                "Id": "sqspolicy",
                "Statement": statements,
            }

            queue.set_attributes(Attributes={"Policy": json.dumps(policy)})

        dead_letter_queue = None
        if dead_letter_queue_name:
            try:
                dead_letter_queue = self.get_queue(dead_letter_queue_name)
            except Exception:
                dead_letter_queue = self._create_queue(
                    dead_letter_queue_name, content_based_deduplication="true"
                )

            redrive_policy = {
                "deadLetterTargetArn": dead_letter_queue.attributes["QueueArn"],
                "maxReceiveCount": "4",
            }

            queue.set_attributes(
                Attributes={"RedrivePolicy": json.dumps(redrive_policy)}
            )

        return queue, dead_letter_queue

    def _create_queue(self, queue_name: str, **kwargs) -> Queue:
        sqs_res = boto3.resource("sqs")
        fifo = queue_name.endswith(".fifo")
        attributes = {}
        if fifo:
            attributes["FifoQueue"] = "true"
            attributes["ContentBasedDeduplication"] = (
                "true" if kwargs.get("content_based_deduplication") else "false"
            )
        queue = sqs_res.create_queue(QueueName=queue_name, Attributes=attributes)
        return queue

    def retrieve_messages(self, queue: Queue, attempt_id=None) -> List[Message]:
        kwargs = dict(
            MaxNumberOfMessages=self.max_number_of_messages,
            VisibilityTimeout=self.visibility_timeout,
            WaitTimeSeconds=self.wait_time_seconds,
            MessageAttributeNames=["All"],
            AttributeNames=["All"],
        )

        if attempt_id:
            kwargs["ReceiveRequestAttemptId"] = attempt_id

        messages = queue.receive_messages(**kwargs)

        # We need to differentiate here whether the message came from SNS or SQS

        return [self._construct_message(message) for message in messages]

    def queue_publish(
        self,
        content: str,
        queue,
        event_type_name: str = None,
        message_group_id: str = None,
        message_deduplication_id: str = None,
    ):
        kwargs = dict(MessageBody=json.dumps({"Message": content}))

        if event_type_name:
            kwargs["MessageAttributes"] = {
                "event_type": {"DataType": "String", "StringValue": event_type_name}
            }

        if message_group_id:
            kwargs["MessageGroupId"] = message_group_id

        if message_deduplication_id:
            kwargs["MessageDeduplicationId"] = message_deduplication_id

        queue.send_message(**kwargs)

    def publish(
        self,
        content: str,
        topic: Topic,
        event_type_name: str,
        extra_attributes: Dict = None,
    ):
        args = dict(
            Message=content,
            MessageAttributes={
                "event_type": {"DataType": "String", "StringValue": event_type_name}
            },
        )

        if extra_attributes:
            if "subject" in extra_attributes:
                args["Subject"] = extra_attributes["subject"]

            if "message_attributes" in extra_attributes:
                args["MessageAttributes"].update(extra_attributes["message_attributes"])

            if "message_structure" in extra_attributes:
                args["MessageStructure"] = extra_attributes["message_structure"]

        response = topic.publish(**args)

        if "MessageId" not in response:
            raise ConnectionError("Could not send the event to the SNS TOPIC")

    def acknowledge(self, message: Message) -> None:
        message.metadata.delete()

    def close_connection(self) -> None:
        pass

    def delete_queue(self, queue: Queue) -> None:
        queue.delete()

    def delete_topic(self, topic: Topic) -> None:
        topic.delete()

    def _construct_message(self, message) -> Message:
        body = message.body
        manifest = ""
        try:
            message_content = json.loads(body)
            if "Message" in message_content:
                content = message_content["Message"]
                # Does the content have more attributes? If so, it is very likely that the message came from a non-raw
                # SNS redirection
                if "MessageAttributes" in message_content:
                    manifest = (
                        message_content["MessageAttributes"]
                        .get("event_type", {})
                        .get("Value")
                        or ""
                    )
            else:
                content = message_content
        except JSONDecodeError:
            content = body

        manifest = (
            manifest
            or message.message_attributes.get("event_type", {}).get("StringValue")
            or ""
        )

        return Message(message.message_id, content, message, manifest)
