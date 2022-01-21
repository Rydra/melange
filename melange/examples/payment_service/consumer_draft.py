from typing import Any, Optional

from melange.consumers import Consumer
from melange.examples.common.commands import DoPayment
from melange.examples.payment_service.events import OrderResponse
from melange.examples.payment_service.service import PaymentService


class PaymentConsumer(Consumer):
    def __init__(self, payment_service: PaymentService):
        super().__init__()
        self.payment_service = payment_service

    def process(self, message: Any, **kwargs: Any) -> None:
        if isinstance(message, OrderResponse):
            self.payment_service.process(message)
        elif isinstance(message, DoPayment):
            self.payment_service.do_payment(message)

    def accepts(self, manifest: Optional[str]) -> bool:
        return manifest in ["OrderResponse", "DoPayment"]
