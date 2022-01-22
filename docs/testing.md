# Testing

Any developer worth its salt does some kind of testing over the code they
develop. However, testing software that spans several processes/threads (like when you do pub/sub over
a queue/topic) can be a daunting task. 

Melange offers several utilities to help you test your publishers
and consumers (or just making everything synchronous inside the context of the
test for the sake of simplicity). Here some examples are presented on how you
could potentially use the library in your tests.

## Asynchronous testing with threads

Follow the next steps whenever you need to have one or more consumers running on the
background of your test:

1. Make sure to create (or ensure that they exist at least) the queues and topics where the 
   message exchange happens.
   
2. Start the consumer loop in a separate thread, and make sure the thread is stopped upon
    termination of the test.
   
3. Call your code that invokes the publishing methods, and have `probes` in place
that poll the environment to check whether the consumers have done their work or not before
doing any kind of assertion that requires of the consumers' results.
   
4. Bonus: After the test is finished, delete the queue/topic to keep the environment clean.
   
Full Example:

``` py title="Asynchronous testing with probes and threads"
--8<-- "tests/doc_examples/test_async.py"
```

This kind of test has the advantage of being very explicit in the sense that it expresses, through the probe,
that this test has some asynchronous processing in the background, and waits for it.
It's quite realistic as well, pub/sub is asynchronous in its nature and we work with
it in this test.

However the arrangement is complex. It's a trade-off between completeness and complexity that you have to embrace
if you want to follow this route.

!!! tip

    Try to abstract away all this arrangement code from the main body of the test
    to keep it clean and clear, avoiding pollution. Testing frameworks have different
    techniques to abstract away arrangements (like pytest fixtures).

## Synchronous testing with the `InMemoryMessagingBackend`

Another option is to use the bundled `InMemoryMessagingBackend` when instantiating your
publishers and consumers. This will make the entirety of the test synchronous in respect
to the message passing.

``` py title="Synchronous testing with the InMemoryMessagingBackend"
--8<-- "tests/doc_examples/test_testing.py"
```

What the `InMemoryMessagingBackend` does, upon
publish, is to store the serialized message in memory and
forward it to the internal consumer dispatcher, so that
the consumers can synchronously receive and process the message.

The `link_synchronously` function is a helper which glues everything together. All the 
messages sent to the queue or topic with
that name will be dispatched to those consumers (if the consumers accept that message).
