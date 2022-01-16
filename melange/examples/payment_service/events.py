from datetime import datetime
from typing import Any, Optional

from simple_cqrs.domain_event import DomainEvent


class OrderResponse(DomainEvent):
    def __init__(
        self, id: str, reference: str, occurred_on: Optional[datetime] = None
    ) -> None:
        super().__init__(occurred_on)
        self.id = id
        self.reference = reference


class OrderStatus(DomainEvent):
    def __init__(
        self,
        order_id: str,
        payment_id: str,
        status: str,
        occurred_on: Optional[datetime] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(occurred_on, **kwargs)
        self.order_id = order_id
        self.payment_id = payment_id
        self.status = status
