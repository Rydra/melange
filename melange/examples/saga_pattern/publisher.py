from melange.examples.common.commands import DoPayment
from melange.message_publisher import SQSPublisher


class SagaPublisher:
    def __init__(self, publisher: SQSPublisher) -> None:
        self.publisher = publisher

    def publish_dopayment(self, do_payment: DoPayment) -> None:
        self.publisher.publish("payment-updates", do_payment)
