# Messaging backends

A **messaging backend** is a wrapper over your message broker. It exposes 
several methods that abstract the broker functionality, making it simpler to work with.

Out of the box Melange provides you with three messaging backends: The `AWSBackend` and 
the `LocalSQSBackend`. The `RabbitMQBackend` is present in the source code, but not actively
maintained. Looking for contributors!

## Writing your own Messaging Backend

Subclass the `MessagingBackend` interface and implement all the methods of that
class. Here is the documentation of the interface class and all its methods. You need
to take in mind, when implementing the methods that return a `QueueWrapper` or a `TopicWrapper`,
to wrap inside them the real object that represents your queue or topic (in your chosen
messaging technology) and unwrap it inside the messaging backend when requiring to perform
specific operations. Look at the `AWSBackend` as a template/example of this wrapping/unwrapping.

::: melange.backends.interfaces
