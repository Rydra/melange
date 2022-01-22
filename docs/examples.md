# Examples

Here are listed some relevant examples that you can find in the source code of Melange,
alongside some explanation. The `MessagingBackend` used for all the examples is the
`LocalSQSBackend`, though you could use your own.

Personally what I do is to spin up a docker-compose process and then run the examples.

# Payment Service

> [Example source](https://github.com/Rydra/melange/tree/main/melange/examples/payment_service)

This is the Melange/python version of the Order/Payment service
that is being implemented in the video series [SAGA Choreography Implementation](https://www.youtube.com/watch?v=WbNJTwKOCuM&t=0s).

The example corresponds to a payment service that listens to a queue that receives
events from an order service (which might come from another external service)
and then those events are consumed to perform more logic.

How to run the example:

1. Run `make run-example-app`. This will start the consumer.
2. On another terminal, run `make run-example-triggerer reference="SOMEREFNUMBER"`

Each time you run the triggerer, you should see a message like `Order SOMEREFNUMBER paid successfully`
pop, meaning that the message was received successfully.


# SAGA Choreography

> [Example source](https://github.com/Rydra/melange/tree/main/melange/examples/saga_pattern)

In this example we will see one powerful usage of melange in the form of a mix of saga 
orchestration/choreography. We will run a SAGA service that will manage the entire order
processing service, and deliver the messages to the appropriate services to run
what could be a fully distributed application.

How to run the example.

1. Run `make run-example-app` to start up the consumer for the payment service.
2. Run `make run-example-saga` to start up the consumer for the saga orchestrator.
3. On another terminal, run `make run-example-saga-triggerer reference="SOMEREFNUMBER"`

What you should see once you run the triggerer is, on the payment service consumer screen,
the confirmation that the order was paid and immediately afterwards, on the saga orchestrator
screen, the message that the order was paid and marked as complete.

Congratulations on running your first web of microservices, connected by a messaging broker with
passing messages!
