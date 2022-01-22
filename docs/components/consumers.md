# Message Dispatchers and Consumers

Message Dispatcher and Consumers are the counterpart of the publishers. 
Consumers attach themselves to a Message Dispatcher, and the message dispatchers start the consuming loop
and receive the messages from a queue, forwarding them to a consumer that accepts
that message.

## Consumers

Consumers are very simple, since they only receive a Message as a parameter and then
they do some kind of processing to send it down to the lower layers of your application (something like a REST view/controller). 
To mplement a consumer with Melange one of the approaches is to subclass the `Consumer` class
and implement the `process` method, and, optionally, the `accepts` method.

Example (from `examples/payment_service/consumer_draft.py`):

``` py
--8<-- "melange/examples/payment_service/consumer_draft.py"
```

There is a variation of the `Consumer`, the `SingleDispatchConsumer` consumer. It relies
on the `singledispatch` library to implement method overloading on the `process` function,
in order to achieve a richer `accepts` and `process` methods. This has proven to make the development
of complex consumers faster and cleaner.

The same `PaymentConsumer` as above, but implemented by subclassing `SingleDispatchConsumer`
(from `examples/payment_service/consumer.py`):

``` py
--8<-- "melange/examples/payment_service/consumer.py"
```

For a consumer to be able to receive messages it requires to be attached to a `MessageDispatcher`

## Message Dispatcher

As summarized on top of this article, the `MessageDispatcher` component/class is the responsible to:

1. Start the polling loop to get new messages through the `MessagingBackend`.
2. Deserialize the message with the appropriate `MessageSerializer`.
3. Pass the message to the consumers that accept it for further processing.
4. Acknowledge the message.

There is a variation of the `MessageDispatcher` called `SimpleMessageDispatcher`
which is essentially the same as the former, but when you have only one consumer.

This is the specification of the `MessageDispatcher` class:

::: melange.message_dispatcher.MessageDispatcher

!!! note

    Unless the `always_ack` is set to `True`, a message will only be acknowleged if
    it's been correcly processed by all consumers that accept the message. 
    Unless [message deduplication](link) is in place, if a consumers fails the same
    message is going to be reprocessed again by all the consumers, which can lead to issues.
    Either use only one consumer per `MessageDispatcher`, make your consumers idempotent,
    or set a `DeduplicationCache` when instantiating the `MessageDispatcher`.
