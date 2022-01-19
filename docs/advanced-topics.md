# Advanced Topics

## Registering the MessagingBackend globally

To instantiate a publishers or a consumer, you need to pass
a `MessagingBackend` as a constructor argument. Depending on the circumstances,
however, this might feel repetitive.

As an alternative, you could use the singleton `BackendManager` and register
a backend for global usage in your initialization code:

``` py
BackendManager().use_backend(SQSBackend())
```

From that point forward, any instantiation of a Publisher or Consumer
does not need a backend as an argument anymore. Revisiting one of the
recurring examples of this documentation, we could use the `BackendManager`
like this.

``` py
from melange.message_publisher import QueuePublisher
from melange.backends.sqs.elasticmq import ElasticMQBackend
from melange.backends.sqs.backend_manager import BackendManager
from melange.serializers.pickle import PickleSerializer

class MyTestMessage:
    def __init__(self, message: str) -> None:
        self.message = message

if __name__ == "__main__":
    backend = ElasticMQBackend(host="localhost", port=9324)
    serializer = PickleSerializer()
    BackendManager().use_backend(backend)
    
    publisher = QueuePublisher(serializer)
    message = MyTestMessage("Hello World!")
    publisher.publish("melangetutorial-queue", message)
    print("Message sent successfully!")
```

Notice that we are not passing the backend now as a parameter
when creating the `QueuePublisher` object, since it will retrieve
it from the BackendManager.

> NOTE: Use the BackendManager with caution though.
> Singletons are [regarded sometimes as an antipattern](https://stackoverflow.com/questions/12755539/why-is-singleton-considered-an-anti-pattern)
depending on the situation, and dependency injection is usually regarded
as a cleaner solution to construct objects.


### Message de-duplication

Distributed architectures are hard, complex and come with a good deal of burdens, but they are required to achieve levels of scalability
and isolation harder to achieve on monolithic architectures. One of this issues is the possibility of
of the same message being received twice by the listeners. Network failures, application crashes, etc...
can cause this issue which, if not though or left undealt can cause your system to be out of sync and
run in an inconsistent state. This is why you need to take measures.

One of this measures is to, simply, write your listeners to be *idempotent*. This means that it does not
matter how many times a listener is called, the result will be the same and it won't impact or leave
the system into an inconsistent state.

However, sometimes writing idempotent code is just not possible. You require **message deduplication** to
account for this and ensure that a message won't be sent twice. You could use Amazon SQS FIFO Queues which
they say they provide this message deduplication, though not only FIFO queues are more expensive than
standard ones, [but exactly-once delivery is just impossible](https://dzone.com/articles/fifo-exactly-once-and-other-costs).
In Melange we have accounted for this with a *Redis cache* that will control that no message is delivered twice.

In order for this to work you have to provide the following environment variables as configuration
so that Melange can connect to your Redis database:

ENVIRONMENT VARIABLE NAME | Default | Description
--- | --- | ---
CACHE_REDIS_HOST | localhost| The host of your Redis
CACHE_REDIS_PORT | 6379 | The port of your Redis
CACHE_REDIS_DB | 0 | The DB to use for your Redis
CACHE_REDIS_PASSWORD | | The password of your Redis
CACHE_NAMESPACE | SimpleCache | You can provide a namespace so that values created by Melange do not collide with each other

If Melange is unable to connect to your Redis it will function normally but you won't enjoy the
benefits of ensuring message deduplication, which may lead your distributed application in an inconsitent
state. You're warned :).
