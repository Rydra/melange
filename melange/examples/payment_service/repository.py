from typing import Dict, Optional

from melange.examples.common.domain import Payment


class PaymentRepository:
    def __init__(self) -> None:
        self.payments: Dict[str, Payment] = {}

    def save(self, payment: Payment) -> None:
        self.payments[payment.id] = payment

    def get(self, id: str) -> Optional[Payment]:
        return self.payments.get(id)
