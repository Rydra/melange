![melange logo](docs/img/melange_logo.png)

# Melange

## A messaging library for an easy inter-communication in distributed architectures 

**Melange** is a python library/framework that abstracts a lot of the boilerplate that is usually 
required to implement a messaging infrastructure (commonly used to create distributed architectures 
and interact with microservices architectures). In a nutshell, it allows you to easily send and receive
messages through a message broker with the help of serializers so that you can communicate your services
through the network.

Out of the box Melange supports Amazon SQS + SNS as messaging backend. Kafka is in the roadmap for
next releases. However the interfaces of this library are designed to extensible and clean should you choose to implement
your own messaging backends and serializers to integrate with Melange.

## Documentation

Full documentation is available at [https://rydra.github.io/melange/](https://rydra.github.io/melange/)

## Installing

```
pip install melange
```

## Trivial example

Publish:

``` python
from simple_cqrs.domain_event import DomainEvent

from melange.backends.sqs.localsqs import LocalSQSBackend
from melange.publishers import QueuePublisher
from melange.serializers.pickle import PickleSerializer
from melange.serializers.registry import SerializerRegistry


class MyTestMessage:
    def __init__(self, message: str) -> None:
        self.message = message


if __name__ == "__main__":
    serializer_settings = {
        "serializers": {"pickle": PickleSerializer},
        "serializer_bindings": {DomainEvent: "pickle"},
    }

    serializer_registry = SerializerRegistry(serializer_settings)

    backend = LocalSQSBackend(host="localhost", port=9324)
    publisher = QueuePublisher(serializer_registry, backend)
    message = MyTestMessage("Hello World!")
    publisher.publish("melangetutorial-queue", message)
    print("Message sent successfully!")
```

Consume:

``` python
from simple_cqrs.domain_event import DomainEvent

from melange.backends.sqs.localsqs import LocalSQSBackend
from melange.consumers import SingleDispatchConsumer, consumer
from melange.examples.doc_examples.tutorial.publish import MyTestMessage
from melange.message_dispatcher import SimpleMessageDispatcher
from melange.serializers.pickle import PickleSerializer
from melange.serializers.registry import SerializerRegistry


class MyConsumer(SingleDispatchConsumer):
    @consumer
    def on_my_test_message_received(self, event: MyTestMessage) -> None:
        print(event.message)


if __name__ == "__main__":
    serializer_settings = {
        "serializers": {"pickle": PickleSerializer},
        "serializer_bindings": {DomainEvent: "pickle"},
    }

    serializer_registry = SerializerRegistry(serializer_settings)

    backend = LocalSQSBackend(host="localhost", port=9324)
    consumer = MyConsumer()
    message_dispatcher = SimpleMessageDispatcher(
        consumer,
        serializer_registry,
        backend=backend,
    )
    print("Consuming...")
    message_dispatcher.consume_loop("melangetutorial-queue")

```

## Why the name 'Melange'

The name "Melange" is a reference to the drug-spice from the sci-fi book saga "Dune", a spice which is only 
generated in a single planet in the universe (planet Dune) and every human depends on it.

>If the spice flows, then the spice can be controlled.  
He who controls the spice, controls the universe.  
The spice must flow.

The analogy can be very well made on Events in a distributed architecture :)

## Project Links

* Docs: [https://rydra.github.io/melange](https://rydra.github.io/melange)

## License

MIT licensed. See the bundled [LICENSE](https://github.com/Rydra/melange/blob/master/LICENSE) file for more details.


_Logo <a href="https://www.vecteezy.com/free-vector/nature">Nature Vectors by Vecteezy</a>_
