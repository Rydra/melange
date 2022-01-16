from typing import Optional

from melange.backends.interfaces import MessagingBackend
from melange.consumer import Consumer, SimpleConsumer, consumer
from melange.event_serializer import MessageSerializer
from melange.examples.common.commands import DoPayment
from melange.examples.payment_service.events import OrderResponse
from melange.examples.payment_service.service import PaymentService
from melange.infrastructure.cache import DedupCache


class PaymentConsumer(Consumer):
    def __init__(self, payment_service: PaymentService):
        self.payment_service = payment_service

    @consumer
    def consume_order_response(self, event: OrderResponse) -> None:
        self.payment_service.process(event)

    @consumer
    def consume_do_payment(self, command: DoPayment) -> None:
        self.payment_service.do_payment(command)


class PaymentSimpleConsumer(SimpleConsumer):
    def __init__(
        self,
        payment_service: PaymentService,
        message_serializer: MessageSerializer,
        cache: Optional[DedupCache] = None,
        backend: Optional[MessagingBackend] = None,
    ):
        super().__init__(message_serializer, cache, backend)
        self.payment_service = payment_service

    @consumer
    def consume_order_response(self, event: OrderResponse) -> None:
        self.payment_service.process(event)

    @consumer
    def consume_do_payment(self, command: DoPayment) -> None:
        self.payment_service.do_payment(command)
