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
