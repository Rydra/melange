# Consumers

Consumers are the counterpart of the publishers. They receive and consume the
messages from a queue, and dispatch the message to a method that handles that message.

To implement a consumer with Melange one of the approaches is to subclass the `Consumer` class
and implement the `process` method.

Example
