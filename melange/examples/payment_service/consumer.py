from melange.consumers import SingleDispatchConsumer, consumer
from melange.examples.common.commands import DoPayment
from melange.examples.payment_service.events import OrderResponse
from melange.examples.payment_service.service import PaymentService


class PaymentConsumer(SingleDispatchConsumer):
    def __init__(self, payment_service: PaymentService):
        super().__init__()
        self.payment_service = payment_service

    @consumer
    def consume_order_response(self, event: OrderResponse) -> None:
        self.payment_service.process(event)

    @consumer
    def consume_do_payment(self, command: DoPayment) -> None:
        self.payment_service.do_payment(command)
