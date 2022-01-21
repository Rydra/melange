# Testing

Any developer worth its salt does some kind of testing over the code they
develop. However, testing software that spans several processes/threads (like when you do pub/sub over
a queue/topic) can be a daunting task. 

Melange offers several utilities to help you test your publishers
and consumers (or just making everything synchronous inside the context of the
test for the sake of simplicity). Here some examples are presented on how you
could potentially use the library in your tests.

## Asynchronous testing with threads

Follow the next steps whenever you need to have one or more consumers running on the
background of your test:

1. Make sure to create (or ensure that they exist at least) the queues and topics where the 
   message exchange happens.
   
2. Start the consumer loop in a separate thread, and make sure the thread is stopped upon
    termination of the test.
   
3. Call your code that invokes the publishing methods, and have `probes` in place
that poll the environment to check whether the consumers have done their work or not before
doing any kind of assertion that requires of the consumers' results.
   
4. Bonus: After the test is finished, delete the queue/topic to keep the environment clean.
   
Full Example:

``` py
import os
import threading
from dataclasses import dataclass
from typing import Optional, Dict

import polling
from hamcrest import *

from melange.backends.factory import MessagingBackendFactory
from melange.backends.sqs.elasticmq import ElasticMQBackend
from melange.consumers import Consumer, SimpleMessageDispatcher
from melange.examples.doc_examples.probe import Probe
from melange.publishers import QueuePublisher
from melange.serializers.pickle import PickleSerializer


class StateProbe(Probe):
    def __init__(
        self, state: "State"
    ) -> None:
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
    threading.Thread(target=lambda: handler.consume_loop(queue_name), daemon=True).start()

    # Publish a message and...
    publisher = QueuePublisher(serializer, backend)
    publisher.publish(queue_name, {"value": 1})

    # ...wait until the value is set
    probe = StateProbe(state)
    probe.wait()

    assert_that(state.value_set, is_(1))

```

This kind of test has the advantage of being very explicit in the sense that it expresses, through the probe,
that this test has some asynchronous processing in the background, and waits for it.
It's quite realistic as well, pub/sub is asynchronous in its nature and we work with
it in this test.

However the arrangement is complex. It's a trade-off between completeness and complexity that you have to embrace
if you want to follow this route.

> TIP: Try to abstract away all this arrangement code from the main body of the test
> to keep it clean and clear, avoiding pollution. Testing frameworks have different
> techniques to abstract away arrangements (like pytest fixtures).

## Synchronous testing with the `InMemoryMessagingBackend`

Another option is to use the bundled `InMemoryMessagingBackend` when instantiating your
publishers and consumers. This will make the entirety of the test synchronous in respect
to the message passing.

``` py
from melange.backends.testing import InMemoryMessagingBackend, link_synchronously
from melange.consumers import Consumer
from melange.publishers import QueuePublisher
from melange.serializers.pickle import PickleSerializer


def test_inmemory_messaging_backend():
    consumer_1 = Consumer(lambda message: print(f"Hello {message['message']}!"))
    consumer_2 = Consumer(lambda message: print(f"Hello {message['message']} 2!"))

    serializer = PickleSerializer()
    backend = InMemoryMessagingBackend()
    link_synchronously("somequeue", [consumer_1, consumer_2], serializer, backend)

    publisher = QueuePublisher(PickleSerializer(), backend=backend)
    publisher.publish("somequeue", {"message": "Mary"})
```

What the `InMemoryMessagingBackend` does, upon
publish, is to store the serialized message in memory and
forward it to the internal consumer dispatcher, so that
the consumers can synchronously receive and process the message.

The `link_synchronously` function is a helper which glues everything together. All the 
messages sent to the queue or topic with
that name will be dispatched to those consumers (if the consumers accept that message).
