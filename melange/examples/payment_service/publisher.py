from melange import QueuePublisher
from melange.examples.payment_service.events import OrderStatus


class PaymentPublisher:
    def __init__(self, publisher: QueuePublisher) -> None:
        self.publisher = publisher

    def publish_orderstatus(self, orderStatus: OrderStatus) -> None:
        self.publisher.publish("order-updates", orderStatus)
        self.publisher.publish("saga-updates", orderStatus)
