# Publishers

Publishers, as implied by the name, publish messages to a message broker,
which are then propagated/stored into a queue for consumers/subscribers to
process.

You can publish messages to queues or topics.

## Publishing to a queue

Publishing a message to a queue makes this message available
to a single consumer (that's the concept of a queue after all).
To do that, build an instance of the `QueuePublisher` class and
call the `publish` method with your message:

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

The `QueuePublisher` requires a [backend](messaging-backends.md) and a 
[serializer](serializers.md) as constructor parameters. The serializer
is necessary to properly serialize and send the message to the messaging backend.

> TIP: In a production project where you would have a proper 
> dependency injection framework in place (e.g. [pinject](https://github.com/google/pinject)), you could instantiate
> the Publisher once and provide that instance through your application


## Publishing to a topic

Publishing a message to a topic works exactly the same way as publishing
to a queue, but it will work with the [Fanout pattern](https://aws.amazon.com/blogs/compute/messaging-fanout-pattern-for-serverless-architectures-using-amazon-sns/)
to distribute the message to several subscribers of that topic.
To do that, build an instance of the `TopicPublisher` class and
call the `publish` method with your message:

``` py
from melange.message_publisher import TopicPublisher
from melange.backends.sqs.elasticmq import ElasticMQBackend
from melange.serializers.pickle import PickleSerializer

class MyTestMessage:
    def __init__(self, message: str) -> None:
        self.message = message

if __name__ == "__main__":
    backend = ElasticMQBackend(host="localhost", port=9324)
    serializer = PickleSerializer()
    publisher = TopicPublisher(serializer, backend)
    message = MyTestMessage("Hello World!")
    publisher.publish("melangetutorial-topic", message)
    print("Message sent successfully!")
```

As you can appreciate it works exactly the same way as publishing to a queue,
the only difference happens behind the scenes.
