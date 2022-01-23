import json
import logging
import uuid
from json import JSONDecodeError
from typing import Any, Dict, Iterable, List, Optional, Tuple

import boto3

from melange.backends.interfaces import MessagingBackend
from melange.models import Message, QueueWrapper, TopicWrapper

logger = logging.getLogger(__name__)


class BaseSQSBackend(MessagingBackend):
    """
    Base class for SQS Backends
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__()
        self.max_number_of_messages = kwargs.get("max_number_of_messages", 10)
        self.visibility_timeout = kwargs.get("visibility_timeout", 100)
        self.wait_time_seconds = kwargs.get("wait_time_seconds", 10)

        self.extra_settings = kwargs.get("extra_settings", {})
        self.sns_settings = kwargs.get("sns_settings", {})

    def declare_topic(self, topic_name: str) -> TopicWrapper:
        sns = boto3.resource("sns", **self.sns_settings)
        topic = sns.create_topic(Name=topic_name)
        return TopicWrapper(topic)

    def get_queue(self, queue_name: str) -> QueueWrapper:
        sqs_res = boto3.resource("sqs", **self.extra_settings)
        return QueueWrapper(sqs_res.get_queue_by_name(QueueName=queue_name))

    def _subscribe_to_topics(
        self, queue: QueueWrapper, topics_to_bind: Iterable[TopicWrapper], **kwargs: Any
    ) -> None:
        if topics_to_bind:
            statements = []
            for topic in topics_to_bind:
                statement = {
                    "Sid": "Sid{}".format(uuid.uuid4()),
                    "Effect": "Allow",
                    "Principal": "*",
                    "Resource": queue.unwrapped_obj.attributes["QueueArn"],
                    "Action": "sqs:SendMessage",
                    "Condition": {
                        "ArnEquals": {"aws:SourceArn": topic.unwrapped_obj.arn}
                    },
                }

                statements.append(statement)

                subscription = topic.unwrapped_obj.subscribe(
                    Protocol="sqs",
                    Endpoint=queue.unwrapped_obj.attributes[
                        "QueueArn"
                    ],  # , Attributes={"RawMessageDelivery": "true"}
                )

                if kwargs.get("filter_events"):
                    filter_policy = {"manifest": kwargs["filter_events"]}
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

            queue.unwrapped_obj.set_attributes(
                Attributes={"Policy": json.dumps(policy)}
            )

    def declare_queue(
        self,
        queue_name: str,
        *topics_to_bind: TopicWrapper,
        dead_letter_queue_name: Optional[str] = None,
        **kwargs: Any,
    ) -> Tuple[QueueWrapper, Optional[QueueWrapper]]:
        try:
            queue = self.get_queue(queue_name)
        except Exception:
            queue = self._create_queue(queue_name, content_based_deduplication="true")

        self._subscribe_to_topics(queue, topics_to_bind, **kwargs)

        dead_letter_queue: Optional[QueueWrapper] = None
        if dead_letter_queue_name:
            try:
                dead_letter_queue = self.get_queue(dead_letter_queue_name)
            except Exception:
                dead_letter_queue = self._create_queue(
                    dead_letter_queue_name, content_based_deduplication="true"
                )

            redrive_policy = {
                "deadLetterTargetArn": dead_letter_queue.unwrapped_obj.attributes[
                    "QueueArn"
                ],
                "maxReceiveCount": "4",
            }

            queue.unwrapped_obj.set_attributes(
                Attributes={"RedrivePolicy": json.dumps(redrive_policy)}
            )

        return queue, dead_letter_queue

    def _create_queue(self, queue_name: str, **kwargs: Any) -> QueueWrapper:
        sqs_res = boto3.resource("sqs", **self.extra_settings)
        fifo = queue_name.endswith(".fifo")
        attributes = {}
        if fifo:
            attributes["FifoQueue"] = "true"
            attributes["ContentBasedDeduplication"] = (
                "true" if kwargs.get("content_based_deduplication") else "false"
            )
        queue = sqs_res.create_queue(QueueName=queue_name, Attributes=attributes)
        return QueueWrapper(queue)

    def retrieve_messages(self, queue: QueueWrapper, **kwargs: Any) -> List[Message]:
        args = dict(
            MaxNumberOfMessages=self.max_number_of_messages,
            VisibilityTimeout=self.visibility_timeout,
            WaitTimeSeconds=self.wait_time_seconds,
            MessageAttributeNames=["All"],
            AttributeNames=["All"],
        )

        if "attempt_id" in kwargs:
            args["ReceiveRequestAttemptId"] = kwargs["attempt_id"]

        messages = queue.unwrapped_obj.receive_messages(**args)

        # We need to differentiate here whether the message came from SNS or SQS
        return [self._construct_message(message) for message in messages]

    def yield_messages(self, queue: QueueWrapper, **kwargs: Any) -> Iterable[Message]:
        args = dict(
            MaxNumberOfMessages=self.max_number_of_messages,
            VisibilityTimeout=self.visibility_timeout,
            WaitTimeSeconds=self.wait_time_seconds,
            MessageAttributeNames=["All"],
            AttributeNames=["All"],
        )

        while True:
            messages = queue.unwrapped_obj.receive_messages(**args)
            for message_content in messages:
                message = self._construct_message(message_content)
                yield message

    def publish_to_queue(
        self, message: Message, queue: QueueWrapper, **kwargs: Any
    ) -> None:
        message_args: Dict = {}
        message_args["MessageBody"] = json.dumps({"Message": message.content})

        is_fifo = queue.unwrapped_obj.attributes.get("FifoQueue") == "true"
        message_deduplication_id = (
            None
            if not is_fifo
            else kwargs.get("message_deduplication_id", str(uuid.uuid4()))
        )

        if message.manifest:
            message_args["MessageAttributes"] = {
                "manifest": {"DataType": "String", "StringValue": message.manifest},
                "serializer_id": {
                    "DataType": "Number",
                    "StringValue": str(message.serializer_id),
                },
            }

        if kwargs.get("message_group_id"):
            message_args["MessageGroupId"] = kwargs["message_group_id"]

        if message_deduplication_id:
            message_args["MessageDeduplicationId"] = message_deduplication_id

        queue.unwrapped_obj.send_message(**message_args)

    def publish_to_topic(
        self,
        message: Message,
        topic: TopicWrapper,
        extra_attributes: Optional[Dict] = None,
    ) -> None:
        args: Dict = dict(
            Message=message.content,
            MessageAttributes={
                "manifest": {
                    "DataType": "String",
                    "StringValue": message.manifest or "",
                },
                "serializer_id": {
                    "DataType": "Number",
                    "StringValue": str(message.serializer_id),
                },
            },
        )

        if extra_attributes:
            if "subject" in extra_attributes:
                args["Subject"] = extra_attributes["subject"]

            if "message_attributes" in extra_attributes:
                args["MessageAttributes"].update(extra_attributes["message_attributes"])

            if "message_structure" in extra_attributes:
                args["MessageStructure"] = extra_attributes["message_structure"]

        response = topic.unwrapped_obj.publish(**args)

        if "MessageId" not in response:
            raise ConnectionError("Could not send the event to the SNS TOPIC")

    def acknowledge(self, message: Message) -> None:
        message.metadata.delete()

    def close_connection(self) -> None:
        pass

    def delete_queue(self, queue: QueueWrapper) -> None:
        queue.unwrapped_obj.delete()

    def delete_topic(self, topic: TopicWrapper) -> None:
        topic.unwrapped_obj.delete()

    def _construct_message(self, message: Any) -> Message:
        body = message.body
        manifest: Optional[str] = None
        serializer_id: Optional[int] = None
        try:
            message_content = json.loads(body)
            if "Message" in message_content:
                content = message_content["Message"]
                # Does the content have more attributes? If so, it is very likely that the message came from a non-raw
                # SNS redirection
                if "MessageAttributes" in message_content:

                    manifest = (
                        message_content["MessageAttributes"]
                        .get("manifest", {})
                        .get("Value")
                        or ""
                    )
                    serializer_id = (
                        message_content["MessageAttributes"]
                        .get("serializer_id", {})
                        .get("Value")
                    )
            else:
                content = message_content
        except JSONDecodeError:
            content = body

        try:
            manifest = manifest or message.message_attributes.get("manifest", {}).get(
                "StringValue"
            )
            serializer_id = int(
                serializer_id
                or message.message_attributes.get("serializer_id", {}).get(
                    "StringValue"
                )
            )
        except Exception:
            manifest = None
            serializer_id = None

        return Message(message.message_id, content, message, serializer_id, manifest)


class AWSBackend(BaseSQSBackend):
    """
    Backend to use with AWS
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
