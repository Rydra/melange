from melange.examples.payment_service.events import OrderResponse
from melange.examples.payment_service.service import PaymentService
from melange.exchange_listener import ExchangeListener, listener


class PaymentConsumer(ExchangeListener):
    def __init__(self, payment_service: PaymentService):
        self.payment_service = payment_service

    @listener
    def consume_order_response(self, event: OrderResponse) -> None:
        self.payment_service.process(event)
