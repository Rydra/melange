import json
import logging
import uuid
from json import JSONDecodeError
from typing import Any, AsyncIterable, Dict, Iterable, List, Optional, Tuple

import aioboto3
import funcy

from melange.backends.interfaces import AsyncMessagingBackend
from melange.models import Message, MessageDto, QueueWrapper, TopicWrapper

logger = logging.getLogger(__name__)


class AsyncBaseSQSBackend(AsyncMessagingBackend):
    """
    Base class for async SQS Backends.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__()
        self.max_number_of_messages = kwargs.get("max_number_of_messages", 10)
        self.visibility_timeout = kwargs.get("visibility_timeout", 100)
        self.wait_time_seconds = kwargs.get("wait_time_seconds", 10)

        self.extra_settings = kwargs.get("extra_settings", {})
        self.sns_settings = kwargs.get("sns_settings", {})
        self.session = aioboto3.Session()

    async def declare_topic(self, topic_name: str) -> TopicWrapper:
        async with self.session.client("sns", **self.sns_settings) as sns:
            topic = await sns.create_topic(Name=topic_name)
            return TopicWrapper(topic)

    async def get_queue(self, queue_name: str) -> QueueWrapper:
        async with self.session.resource("sqs", **self.extra_settings) as sqs:
            queue = await sqs.get_queue_by_name(QueueName=queue_name)
            return QueueWrapper(queue)

    async def get_queue_attributes(self, queue: QueueWrapper) -> Dict:
        async with self.session.client("sqs", **self.extra_settings) as sqs:
            return (
                await sqs.get_queue_attributes(
                    QueueUrl=queue.unwrapped_obj.url, AttributeNames=["All"]
                )
            )["Attributes"]

    async def set_queue_attributes(self, queue: QueueWrapper, attributes: Dict) -> None:
        async with self.session.client("sqs", **self.extra_settings) as sqs:
            await sqs.set_queue_attributes(
                QueueUrl=queue.unwrapped_obj.url, Attributes=attributes
            )

    async def _subscribe_to_topics(
        self, queue: QueueWrapper, topics_to_bind: Iterable[TopicWrapper], **kwargs: Any
    ) -> None:
        async with self.session.client("sns", **self.extra_settings) as sns:
            attributes = await self.get_queue_attributes(queue)
            if topics_to_bind:
                statements = []
                for topic in topics_to_bind:
                    statement = {
                        "Sid": "Sid{}".format(uuid.uuid4()),
                        "Effect": "Allow",
                        "Principal": "*",
                        "Resource": attributes["QueueArn"],
                        "Action": "sqs:SendMessage",
                        "Condition": {
                            "ArnEquals": {
                                "aws:SourceArn": topic.unwrapped_obj["TopicArn"]
                            }
                        },
                    }

                    statements.append(statement)

                    subscription = await sns.subscribe(
                        TopicArn=topic.unwrapped_obj["TopicArn"],
                        Protocol="sqs",
                        Endpoint=attributes[
                            "QueueArn"
                        ],  # , Attributes={"RawMessageDelivery": "true"}
                    )

                    if kwargs.get("filter_events"):
                        filter_policy = {"manifest": kwargs["filter_events"]}
                    else:
                        filter_policy = {}

                    await sns.set_subscription_attributes(
                        SubscriptionArn=subscription["SubscriptionArn"],
                        AttributeName="FilterPolicy",
                        AttributeValue=json.dumps(filter_policy),
                    )

                policy = {
                    "Version": "2012-10-17",
                    "Id": "sqspolicy",
                    "Statement": statements,
                }

                await self.set_queue_attributes(queue, {"Policy": json.dumps(policy)})

    async def declare_queue(
        self,
        queue_name: str,
        *topics_to_bind: TopicWrapper,
        dead_letter_queue_name: Optional[str] = None,
        **kwargs: Any,
    ) -> Tuple[QueueWrapper, Optional[QueueWrapper]]:
        try:
            queue = await self.get_queue(queue_name)
        except Exception:
            queue = await self._create_queue(
                queue_name, content_based_deduplication="true"
            )

        await self._subscribe_to_topics(queue, topics_to_bind, **kwargs)

        dead_letter_queue: Optional[QueueWrapper] = None
        if dead_letter_queue_name:
            try:
                dead_letter_queue = await self.get_queue(dead_letter_queue_name)
            except Exception:
                dead_letter_queue = await self._create_queue(
                    dead_letter_queue_name, content_based_deduplication="true"
                )

            attributes = await self.get_queue_attributes(dead_letter_queue)

            redrive_policy = {
                "deadLetterTargetArn": attributes["QueueArn"],
                "maxReceiveCount": "4",
            }

            await self.set_queue_attributes(
                queue, {"RedrivePolicy": json.dumps(redrive_policy)}
            )

        return queue, dead_letter_queue

    async def _create_queue(self, queue_name: str, **kwargs: Any) -> QueueWrapper:
        async with self.session.resource("sqs", **self.extra_settings) as sqs_res:
            fifo = queue_name.endswith(".fifo")
            attributes = {}
            if fifo:
                attributes["FifoQueue"] = "true"
                attributes["ContentBasedDeduplication"] = (
                    "true" if kwargs.get("content_based_deduplication") else "false"
                )
            queue = await sqs_res.create_queue(
                QueueName=queue_name, Attributes=attributes
            )
            return QueueWrapper(queue)

    async def retrieve_messages(
        self, queue: QueueWrapper, **kwargs: Any
    ) -> AsyncIterable[Message]:
        args = dict(
            MaxNumberOfMessages=self.max_number_of_messages,
            VisibilityTimeout=self.visibility_timeout,
            WaitTimeSeconds=self.wait_time_seconds,
            MessageAttributeNames=["All"],
            AttributeNames=["All"],
        )

        if "attempt_id" in kwargs:
            args["ReceiveRequestAttemptId"] = kwargs["attempt_id"]

        async with self.session.client("sqs", **self.extra_settings) as client:
            messages = await client.receive_message(
                QueueUrl=queue.unwrapped_obj.url, **args
            )

            for message in messages.get("Messages", []):
                yield self._construct_message_from_raw(message, queue.unwrapped_obj.url)

    async def yield_messages(
        self, queue: QueueWrapper, **kwargs: Any
    ) -> AsyncIterable[Message]:
        while True:
            async for message in self.retrieve_messages(queue, **kwargs):
                yield message

    async def publish_to_queue(
        self, message: Message, queue: QueueWrapper, **kwargs: Any
    ) -> None:
        message_args: Dict = {}
        message_args["MessageBody"] = json.dumps({"Message": message.content})

        attributes = await self.get_queue_attributes(queue)
        is_fifo = attributes.get("FifoQueue") == "true"
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

        async with self.session.client("sqs", **self.extra_settings) as client:
            await client.send_message(QueueUrl=queue.unwrapped_obj.url, **message_args)

    async def publish_to_queue_batch(
        self, message_dtos: List[MessageDto], queue: QueueWrapper
    ) -> None:
        attributes = await self.get_queue_attributes(queue)
        for chunk in funcy.chunks(10, message_dtos):
            entries: List[Dict[str, Any]] = []

            for message_dto in chunk:
                message = message_dto.message
                entry: Dict = {}
                entry["MessageBody"] = json.dumps({"Message": message.content})

                is_fifo = attributes.get("FifoQueue") == "true"
                message_deduplication_id = (
                    None
                    if not is_fifo
                    else (message_dto.message_deduplication_id or str(uuid.uuid4()))
                )

                if message.manifest:
                    entry["MessageAttributes"] = {
                        "manifest": {
                            "DataType": "String",
                            "StringValue": message.manifest,
                        },
                        "serializer_id": {
                            "DataType": "Number",
                            "StringValue": str(message.serializer_id),
                        },
                    }

                if message_dto.message_group_id:
                    entry["MessageGroupId"] = message_dto.message_group_id

                if message_deduplication_id:
                    entry["MessageDeduplicationId"] = message_deduplication_id

                entry["Id"] = str(uuid.uuid4())
                entries.append(entry)

            async with self.session.client("sqs", **self.extra_settings) as client:
                await client.send_message_batch(
                    QueueUrl=queue.unwrapped_obj.url, Entries=entries
                )

    async def publish_to_topic(
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

        async with self.session.client("sns", **self.extra_settings) as sns:
            response = await sns.publish(
                TopicArn=topic.unwrapped_obj["TopicArn"], **args
            )

        if "MessageId" not in response:
            raise ConnectionError("Could not send the event to the SNS TOPIC")

    async def acknowledge(self, message: Message) -> None:
        async with self.session.client("sqs", **self.extra_settings) as client:
            await client.delete_message(
                QueueUrl=message.metadata["QueueUrl"],
                ReceiptHandle=message.metadata["ReceiptHandle"],
            )

    async def acknowledge_batch(self, messages: List[Message]) -> None:
        if not messages:
            return

        queue_url = messages[0].metadata["QueueUrl"]
        async with self.session.client("sqs", **self.extra_settings) as client:
            for chunk in funcy.chunks(10, messages):
                await client.delete_message_batch(
                    QueueUrl=queue_url,
                    Entries=[
                        {
                            "Id": str(uuid.uuid4()),
                            "ReceiptHandle": message.metadata["ReceiptHandle"],
                        }
                        for message in chunk
                    ],
                )

    def close_connection(self) -> None:
        pass

    async def get_queue_url(self, queue_name: str) -> str:
        """
        Most of the boto client calls require the queue url as a parameter,
        so it is useful to have this kind of method which, given a name,
        gives you back the URL
        """
        async with self.session.client("sqs", **self.extra_settings) as client:
            response = await client.get_queue_url(QueueName=queue_name)
            return response["QueueUrl"]

    async def delete_queue(self, queue: QueueWrapper) -> None:
        async with self.session.client("sqs", **self.extra_settings) as client:
            await client.delete_queue(QueueUrl=queue.unwrapped_obj.url)

    async def delete_topic(self, topic: TopicWrapper) -> None:
        async with self.session.client("sns", **self.extra_settings) as client:
            await client.delete_topic(TopicArn=topic.unwrapped_obj["TopicArn"])

    def _construct_message_from_raw(self, message: Dict, queue_url: str) -> Message:
        body = message["Body"]
        manifest: Optional[str] = None
        serializer_id: Optional[int] = None
        try:
            message_content = json.loads(body)
            if "Message" in message_content:
                # If we reach this point, it means that this message has come
                # from SNS, and the contents lie in a different structure
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
                attributes = message["MessageAttributes"]
                manifest = manifest or attributes.get("manifest", {}).get("StringValue")
                serializer_id = int(
                    serializer_id
                    or attributes.get("serializer_id", {}).get("StringValue")
                )
        except JSONDecodeError:
            content = body

        message_id = message["MessageId"]
        message["QueueUrl"] = queue_url

        return Message(message_id, content, message, serializer_id, manifest)


class AsyncLocalSQSBackend(AsyncBaseSQSBackend):
    """
    Local backend to use with elasticMQ
    """

    def __init__(self, **kwargs: Any) -> None:

        super().__init__(
            extra_settings=dict(
                endpoint_url=f"{kwargs.get('host', 'localhost')}:{kwargs.get('port', 4566)}",
                region_name="us-east-1",
                aws_secret_access_key="x",
                aws_access_key_id="x",
                use_ssl=False,
            ),
            sns_settings=dict(
                endpoint_url=f"{kwargs.get('sns_host', 'localhost')}:{kwargs.get('sns_port', 4566)}",
                aws_secret_access_key="x",
                aws_access_key_id="x",
                region_name="us-east-1",
                use_ssl=False,
            ),
            **kwargs,
        )
