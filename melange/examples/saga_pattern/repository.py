from typing import Dict, Optional

from melange.examples.saga_pattern.models import Saga


class SagaRepository:
    def __init__(self) -> None:
        self.sagas: Dict[str, Saga] = {}

    def save(self, payment: Saga) -> None:
        self.sagas[payment.id] = payment

    def get(self, id: str) -> Optional[Saga]:
        return self.sagas.get(id)
