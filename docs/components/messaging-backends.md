# Messaging backends

A **messaging backend** is a wrapper over your message broker. It exposes 
several methods that abstract the broker functionality, making it simpler to work with.

Out of the box Melange provides you with three messaging backends: The `AWSBackend`,
the `RabbitMQBackend` and the `LocalSQSBackend`.

## Writing your own Messaging Backend

Subclass the `MessagingBackend` interface and implement all the methods of that
class. Here is the documentation of the interface class and all its methods:

::: melange.backends.interfaces
