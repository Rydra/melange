# Tutorial - Getting started

> Talk is cheap. show me the code.
> 
> *- Linus Torvalds -*

Event-driven architectures work with the Publish/Subscribe pattern to achieve decoupling.
With this pattern, publishers and subscribers do not know about each other while they can exchange
information among them. In order to achieve this and communicate effectively a 
mediator, or better said, a **Message Broker** is required to transfer messages from
publishers to subscribers. Clients can subscribe this broker, waiting for events they are interested in,
or publish messages so that the broker can distribute these messages appropriately.

This tutorial assumes that you have basic understanding of the pub/sub
mechanics. If not, there are a whole bunch of resources to get your feet
wet on the topic. Also it's good to have `docker` installed since we are
going to spin up local infrastructure to serve as a messaging broker.

## Choosing a Messaging Backend

A messaging backend is the infrastructure where your messages are going to be published
and consumed. In this tutorial we are going to use [LocalStack](https://github.com/localstack/localstack)
as our messaging backend. Basically spinning up an ElasticMQ (for example with `docker-compose`) 
in your machine will provide you with a local SQS+SNS for development with boto, which
makes it ideal for testing and for the sake of this tutorial. You could follow the instructions
in the LocalStack project to install it to your local machine. Though the quickest route
is to launch the docker image with melange:

```
docker-compose up
```

This will start LocalStack in the port `4566` in `localhost`, ready to be used.

## Creating a queue

Before using a queue you need to create it. Put the following code snippet into a
file called `create_queue.py` and execute it to create the queue:

``` py
--8<-- "melange/examples/doc_examples/tutorial/create_queue.py"
```

## Publishing messages

Publishing messages to a queue with Melange is easy. Just create an instance of the message
publisher and `publish` the message. Put the following code snippet into a file called `publish_example.py`:

``` py
--8<-- "melange/examples/doc_examples/tutorial/publish.py"
```

Once you run this code it will publish a message `MyTestMessage` with the contents `Hello World` in
the queue `melangetutorial-queue`.
You can send anything as long as the `SerializerRegistry` can serialize/deserialize
the object. Refer [Serialization](../components/serialization.md) for further details.

!!! note

    For the sake of this tutorial you can use simple config which just uses the `PickleSerializer` 
    to serialize your messages. For production applications however you should probably use another 
    type of serializer or create your own, since `pickle` is [considered unsafe](https://docs.python.org/3/library/pickle.html) and
    only works with python consumers. Consider creating your own serializer or use the
    `JsonSerializer` at the very least once you put Melange in production.


## Consuming messages

It's good to publish messages, but they are worth nothing if nobody reads them. Therefore,
we need a consumer that reads these messages and reacts to them.

Put the following code snippet in a file called `consumer-example.py` and run it:

``` py
--8<-- "melange/examples/doc_examples/tutorial/consume.py"
```

Upon hitting the `consume_loop` method, the process will start polling the queue for new
messages. Once it receives a message, as long as the message is of type `MyTestMessage` it will
forward this message to the `MyConsumer`. If your infrastructure was set correctly, every time
you run the `publish_example.py` script you will see a print with the message on the screen where
the consumer is running.

Congratulations! You just run your very first example of a Pub/Sub mechanism with Melange!

!!! note

    It's a good idea to have shared classes (like the `MyTestMessage` in the example) in its
    own python module (e.g. `shared.py`)

## Where to go from here

Now that you grasped the basic idea on how you could use Melange, you could go further and read more
details about:

* [Consumers](../components/consumers.md)
* [Publishers](../components/publishers.md)
* [Messaging Backend](../components/messaging-backends.md)
* [Seriatization](../components/serialization.md)

To add to that, although the exposed example is quite simple, it serves as the foundation to implement a number of
use cases and distributed architectures with microservices. With Melange you can:

* Build a CQRS + Event sourcing architecture, where you publish your events to a queue or topic from the Command
side and read those with a consumer from the Read side to create your data projections.
* Build choreography Sagas for long-running processes which can span several transactions.
* Implement microservices which consume messages from a queue to do their job (e.g. an staticstics microservice
  that reacts to a `OrderCreated` event and increments a counter to track how many orders your system has).
  
We have not covered the case of topics. Refer to [Publishers](../components/publishers.md) for further details.

In addition, Melange is bundled with a consumer that works with a python application. But the consumer
can be implemented in any language and any technology that can read messages from your queue (AWS Lambda, Azure functions, 
a NodeJS app...)
