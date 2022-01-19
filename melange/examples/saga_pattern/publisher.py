from melange.examples.common.commands import DoPayment
from melange.publishers import QueuePublisher


class SagaPublisher:
    def __init__(self, publisher: QueuePublisher) -> None:
        self.publisher = publisher

    def publish_dopayment(self, do_payment: DoPayment) -> None:
        self.publisher.publish("payment-updates", do_payment)
