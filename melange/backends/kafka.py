from typing import Dict

from melange.backends.interfaces import MessagingBackend


class KafkaBackend(MessagingBackend):
    """
    TODO

    Kafka works differently than, say, SQS. You connect with the Kafka consumer
    to a list of topics, and then you iterate over them to obtain the messages
    """

    def __init__(self, config: Dict) -> None:
        super().__init__()
        self.config = config

    # def retrieve_messages(self, queue: QueueWrapper, **kwargs: Any) -> List[Message]:
    #     kwargs = {}
    #     if "security.protocol" in self.config:
    #         kwargs["security_protocol"] = self.config["security.protocol"]
    #
    #     consumer = KafkaConsumer(
    #         *topics,
    #         group_id=self.config["group.id"],
    #         bootstrap_servers=self.config["bootstrap.servers"],
    #         default_offset_commit_callback=self.config["on_commit"],
    #         **kwargs,
    #     )
    #
    #     for msg in consumer:
    #         yield msg
