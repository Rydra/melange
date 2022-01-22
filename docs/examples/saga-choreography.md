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
