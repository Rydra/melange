import os

import pytest
from hamcrest import *

from melange.backends.factory import MessagingBackendFactory
from melange.backends.sqs.elasticmq import LocalSQSBackend


class TestFactory:
    @pytest.fixture
    def backend(self):
        return LocalSQSBackend(
            wait_time_seconds=1,
            visibility_timeout=10,
            host=os.environ.get("SQSHOST"),
            port=os.environ.get("SQSPORT"),
            sns_host=os.environ.get("SNSHOST"),
            sns_port=os.environ.get("SNSPORT"),
        )

    def test_create_topic(self, backend):
        factory = MessagingBackendFactory(backend=backend)
        topic = factory.init_topic("mytopic")
        assert_that(topic.unwrapped_obj, is_not(none()))

    def test_create_and_subscribe_queue_with_a_topic(self, backend):
        factory = MessagingBackendFactory(backend=backend)
        queue = factory.init_queue("myqueue", ["mytopic1", "mytopic2"], "mydlq")
        assert_that(queue.unwrapped_obj, is_not(none()))
