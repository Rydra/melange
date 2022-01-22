# Factory

Although you could set up your own topics and queues in your infrastructure
(e.g. by using terraform) you can rely on 

Personally I have no strong feelings over defining your queues and topics through
an infrastructure-as-code framework or letting the application create it's own
queues and topics (as long as it has the appropriate permissions to do so). In any
case, Melange offers a factory to create queues and topics for you with the
`MessagingBackendFactory`.

The factory initialization methods are idempotent. If a queue or a topic already exist, they will 
keep the same queue or topic, but override any settings or customizations that you
might have manually set in your PaaS platform. 

## Creating a queue

Let's say you'd wish to create an Amazon SQS queue to listen to the events for a 
payment service. You could invoke the factory as follows:


``` py
--8<-- "melange/examples/doc_examples/factory_queue.py"
```

This will create a FIFO queue `payment-updates` in your AWS account (remember to
appropriately set the AWS variables since the SQS backend uses `boto` behind the
scenes).

You could also define a dead letter queue for messages that could not
be delivered successfully:

``` py
factory.init_queue("payment-updates.fifo", dead_letter_queue_name="payment-updates.fifo")
```

## Creating a topic

Topics apply the fan-out pattern to send the message to anyone who is subscribed
to them. They are useful to decouple your consumers from your application
so that they don't need to know who they are sending their messages to. With
the factory you could create a topic like this:

``` py
--8<-- "melange/examples/doc_examples/factory_topic.py"
```


## Creating a queue and subscribing it to several topics

You could create a queue and immediately subscribe it to a number of topics:

``` py
--8<-- "melange/examples/doc_examples/factory_complete.py"
```

This will create the topics `my-topic-1`, `my-topic-2` and `my-topic-3`,
then create the `payment-updates.fifo` queue, and subscribe it to the
aforementioned topics. It will create the dead letter queue too.
