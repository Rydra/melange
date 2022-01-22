# Examples

Here are listed some relevant examples that you can find in the source code of Melange,
alongside some explanation. The `MessagingBackend` used for all the examples is the
`LocalSQSBackend`, though you could use your own.

Personally what I do is to spin up a docker-compose process and then run the example.

# Payment Service

> [Example source](https://github.com/Rydra/melange/tree/main/melange/examples/payment_service)

This is the Melange/python version of the Order/Payment service
that is being implemented in the video series [SAGA Choreography Implementation](https://www.youtube.com/watch?v=WbNJTwKOCuM&t=0s).

The example corresponds to a payment service that listens to a queue that receives
events from an order service (which might come from another external service)
and then those events are consumed to perform more logic.

To run the example, execute the `app.py`, which will start up the consumer. Afterwards,
each time you trigger
