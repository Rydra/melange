from typing import Dict, Optional


class SagaState:
    FAILED = "failed"
    COMPLETED = "completed"
    RUNNING = "running"


class Saga:
    def __init__(self, id: str, data: Optional[Dict] = None) -> None:
        self.id = id
        self.data = data
        self.state = SagaState.RUNNING

    def complete(self) -> None:
        self.state = SagaState.COMPLETED

    def fail(self) -> None:
        self.state = SagaState.FAILED
