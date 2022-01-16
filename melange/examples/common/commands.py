from datetime import datetime
from typing import Any, Optional

from simple_cqrs.domain_event import DomainEvent


class DoPayment(DomainEvent):
    def __init__(
        self,
        order_id: str,
        reference: str,
        occurred_on: Optional[datetime] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(occurred_on, **kwargs)
        self.order_id = order_id
        self.reference = reference
