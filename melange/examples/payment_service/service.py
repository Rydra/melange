import uuid
from datetime import datetime

from melange.examples.common.commands import DoPayment
from melange.examples.common.domain import Payment
from melange.examples.payment_service.events import OrderResponse, OrderStatus
from melange.examples.payment_service.publisher import PaymentPublisher
from melange.examples.payment_service.repository import PaymentRepository


class PaymentService:
    def __init__(
        self, payment_repository: PaymentRepository, payment_publisher: PaymentPublisher
    ) -> None:
        self.payment_repository = payment_repository
        self.payment_publisher = payment_publisher

    def process(self, order_response: OrderResponse) -> None:
        payment = Payment(
            str(uuid.uuid4()), order_response.id, "SUCCESS", datetime.now()
        )
        self.payment_repository.save(payment)

        order_status = OrderStatus(
            order_id=payment.order_id, payment_id=payment.id, status="ORDER_PAID"
        )
        print(f"Order {order_response.reference} paid successfully")
        self.payment_publisher.publish_orderstatus(order_status)

    def do_payment(self, do_payment: DoPayment) -> None:
        payment = Payment(
            str(uuid.uuid4()), do_payment.order_id, "SUCCESS", datetime.now()
        )
        self.payment_repository.save(payment)

        order_status = OrderStatus(
            order_id=payment.order_id,
            payment_id=payment.id,
            status="ORDER_PAID",
            correlation_id=do_payment.correlation_id,
        )
        print(f"Order {do_payment.reference} paid successfully")
        self.payment_publisher.publish_orderstatus(order_status)
