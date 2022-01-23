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
--8<-- "melange/examples/doc_examples/tutorial/publish.py"
```

The `QueuePublisher` requires a [backend](messaging-backends.md) and the 
[serializer registry](serialization.md) as constructor parameters. The serializer
registry is necessary to properly serialize and send the message to the messaging backend.

!!! tip

    In a production project where you would have a proper 
    dependency injection framework in place (e.g. [pinject](https://github.com/google/pinject)), you could instantiate
    the Publisher once and provide that instance through your application


## Publishing to a topic

Publishing a message to a topic works exactly the same way as publishing
to a queue, but it will work with the [Fanout pattern](https://aws.amazon.com/blogs/compute/messaging-fanout-pattern-for-serverless-architectures-using-amazon-sns/)
to distribute the message to several subscribers of that topic.
To do that, build an instance of the `TopicPublisher` class and
call the `publish` method with your message:

``` py
--8<-- "melange/examples/doc_examples/topic_publish.py"
```

As you can appreciate it works exactly the same way as publishing to a queue,
the only difference happens behind the scenes.
