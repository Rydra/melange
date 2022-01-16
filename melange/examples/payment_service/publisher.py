from melange.examples.payment_service.events import OrderStatus
from melange.message_publisher import SQSPublisher


class PaymentPublisher:
    def __init__(self, publisher: SQSPublisher) -> None:
        self.publisher = publisher

    def publish_orderstatus(self, orderStatus: OrderStatus) -> None:
        self.publisher.publish("order-updates", orderStatus)
        self.publisher.publish("saga-updates", orderStatus)