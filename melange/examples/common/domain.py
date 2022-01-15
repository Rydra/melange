from dataclasses import dataclass
from datetime import datetime


@dataclass
class Payment:
    id: str
    order_id: str
    status: str
    created: datetime
