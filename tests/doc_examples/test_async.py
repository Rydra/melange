import os
import threading
from dataclasses import dataclass
from typing import Dict, Optional

import polling
from hamcrest import *

from melange.backends.factory import MessagingBackendFactory
from melange.backends.sqs.elasticmq import ElasticMQBackend
from melange.consumers import Consumer
from melange.message_dispatcher import SimpleMessageDispatcher
from melange.publishers import QueuePublisher
from melange.serializers.pickle import PickleSerializer
from tests.probe import Probe


class StateProbe(Probe):
    def __init__(self, state: "State") -> None:
        self.state = state

    def sample(self) -> None:
        pass

    def can_be_measured(self) -> bool:
        self.sample()
        return self.state.value_set is not None

    def wait(self) -> None:
        try:
            polling.poll(self.can_be_measured, 1, timeout=60)
        except polling.TimeoutException as e:
            raise Exception("Timeout!") from e


@dataclass
class State:
    value_set: Optional[int] = None


def test_async_consumer(request):
    serializer = PickleSerializer()

    # We'll use the ElasticMQ as backend since it works like a real SQS queue
    backend = ElasticMQBackend(
        host=os.environ.get("SQSHOST"), port=os.environ.get("SQSPORT")
    )
    queue_name = "testqueue"

    # Initialize the queue
    queue = MessagingBackendFactory(backend).init_queue(queue_name)

    # Delete the queue upon finishing the execution of the test
    def teardown():
        backend.delete_queue(queue)

    request.addfinalizer(teardown)

    # Create a consumer that, upon receiving a message, will set
    # the variable "value set" to later assert that this value
    # has, indeed, been set by the consumer that is running on another thread
    state = State()

    def set_state(message: Dict) -> None:
        state.value_set = message["value"]

    consumer = Consumer(on_message=set_state)
    handler = SimpleMessageDispatcher(consumer, serializer, backend=backend)
    # Start the consumer loop thread to run the consumer loop in the background
    threading.Thread(
        target=lambda: handler.consume_loop(queue_name), daemon=True
    ).start()

    # Publish a message and...
    publisher = QueuePublisher(serializer, backend)
    publisher.publish(queue_name, {"value": 1})

    # ...wait until the value is set
    probe = StateProbe(state)
    probe.wait()

    assert_that(state.value_set, is_(1))
