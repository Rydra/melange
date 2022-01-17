# Tutorial - Getting started

This tutorial assumes that you have basic understanding of the pub/sub
mechanics. If not, there are a whole bunch of resources to get your feet
wet on the topic. Also it's good to have `docker` installed since we are
going to spin up local infrastructure to serve as a messaging broker.


## Choosing a Messaging Backend

A messaging backend is the infrastructure where your messages are going to be published
and consumed. In this tutorial we are going to use [ElasticMQ](https://github.com/softwaremill/elasticmq)
as our messaging backend. Basically spinning up an ElasticMQ (for example with `docker-compose`) 
in your machine will provide you with an SQS-like infrastructure to use with boto, which
makes it ideal for testing and for the sake of this tutorial. You could follow the instructions
in the ElasticMQ project to install it to your local machine. Though the quickest route
is to launch the docker image:

```
docker run -p 9324:9324 -p 9325:9325 softwaremill/elasticmq-native
```

This will start ElasticMQ in the port `9324` in `localhost`, ready to be used.

## Creating a queue

Before using a queue you need to create it. Put the following code snippet into a
file called `create_queue.py` and execute it to create the queue:

``` py
from melange.backends.sqs.elasticmq import ElasticMQBackend
from melange.backends.factory import MessagingBackendFactory

backend = ElasticMQBackend(host="localhost", port=9324)
factory = MessagingBackendFactory(backend)
factory.init_queue("melangetutorial-queue")
```

## Publishing messages

Publishing messages to a queue with Melange is easy. Just create an instance of the message
publisher and `publish` the message. Put the following code snippet into a file called `publish_example.py`:

``` py
from melange.message_publisher import QueuePublisher
from melange.backends.sqs.elasticmq import ElasticMQBackend
from melange.serializers.pickle import PickleSerializer

class MyTestMessage:
    def __init__(self, message: str) -> None:
        self.message = message

if __name__ == "__main__":
    backend = ElasticMQBackend(host="localhost", port=9324)
    serializer = PickleSerializer()
    publisher = QueuePublisher(serializer, backend)
    message = MyTestMessage("Hello World!")
    publisher.publish("melangetutorial-queue", message)
    print("Message sent successfully!")
```

Once you run this code it will publish a message `MyTestMessage` with the contents `Hello World` in
the queue `melangetutorial-queue`.
You can send anything as long as your selected serializer can serialize/deserialize
the object. Refer [Serializers](components/serializers.md) for further details.

> NOTE: For the sake of this tutorial you can use the `PickleSerializer` to serialize your messages.
For production applications however you should probably use another type of serializer or create your own,
since `pickle` is [considered unsafe](https://docs.python.org/3/library/pickle.html) and
only works with python consumers.


## Consuming messages

It's good to publish messages, but they are worth nothing if nobody reads them. Therefore,
we need a consumer that reads these messages and reacts to them.

Put the following code snippet in a file called `consumer-example.py` and run it:

``` py
from melange.consumers import Consumer, ConsumerHandler
from melange.backends.sqs.elasticmq import ElasticMQBackend
from melange.serializers.pickle import PickleSerializer
from publish_example import MyTestMessage

class MyConsumer(SingleDispatchConsumer):
    @listener
    def on_my_test_message_received(self, event: MyTestMessage) -> None:
        print(event.message)
        
if __name__ == "__main__":
    backend = ElasticMQBackend(host="localhost", port=9324)
    serializer = PickleSerializer()
    consumer = MyConsumer()
    consumer_handler = SimpleConsumerHandler(
        serializer,
        backend=backend,
    )
    print("Consuming...")
    payment_consumer.consume_loop("melangetutorial-queue")
```

Upon hitting the `consume_loop` method, the process will start polling the queue for new
messages. Once it receives a message, as long as the message is of type `MyTestMessage` it will
forward this message to the `MyConsumer`. If your infrastructure was set correctly, every time
you run the `publish_example.py` script you will see a print with the message on the screen where
the consumer is running.

Congratulations! You just run your very first example of a Pub/Sub mechanism with Melange!

> NOTE: It's a good idea to have shared classes (like the `MyTestMessage` in the example) in its
> own python module (e.g. `shared.py`)

## Where to go from here

Although the exposed example is quite simple, it serves as the foundation to implement a number of
use cases and distributed architectures with microservices. With Melange you can:

* Build a CQRS + Event sourcing architecture, where you publish your events to a queue or topic from the Command
side and read those with a consumer from the Read side to create your data projections.
* Build choreography Sagas for long-running processes which can span several transactions.
* Implement microservices which consume messages from a queue to do their job (e.g. an staticstics microservice
  that reacts to a `OrderCreated` event and increments a counter to track how many orders your system has).

Also we have not covered the case of topics. Refer to [Advanced Topics](advanced-topics.md) for further details.
