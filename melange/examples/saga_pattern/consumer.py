import uuid
from typing import Any

from melange import SingleDispatchConsumer, consumer
from melange.examples.common.commands import DoPayment
from melange.examples.payment_service.events import OrderResponse, OrderStatus
from melange.examples.saga_pattern.models import Saga
from melange.examples.saga_pattern.publisher import SagaPublisher
from melange.examples.saga_pattern.repository import SagaRepository


class SagaConsumer(SingleDispatchConsumer):
    def __init__(
        self,
        saga_repository: SagaRepository,
        saga_publisher: SagaPublisher,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.saga_repository = saga_repository
        self.saga_publisher = saga_publisher

    @consumer
    def on_order_response(self, event: OrderResponse) -> None:
        print(f"Sending payment for order {event.reference}")
        saga = Saga(
            str(uuid.uuid4()),
            data={"order_id": event.id},
        )
        self.saga_repository.save(saga)

        command = DoPayment(
            order_id=event.id, reference=event.reference, correlation_id=saga.id
        )
        self.saga_publisher.publish_dopayment(command)

    @consumer
    def on_order_status(self, event: OrderStatus) -> None:
        print(f"Order received with status: {event.status}")
        saga = self.saga_repository.get(event.correlation_id)
        if not saga:
            return

        print(f"Marking saga {event.correlation_id} as COMPLETED")
        saga.complete()
        self.saga_repository.save(saga)
