import argparse
import os
import uuid

from melange import QueuePublisher
from melange.backends import LocalSQSBackend
from melange.examples.payment_service.events import OrderResponse
from melange.examples.shared import serializer_registry
from melange.serializers import PickleSerializer

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Triggers an order event for the payment service to collect"
    )
    parser.add_argument("reference", type=str, help="The reference number of the order")
    args = parser.parse_args()

    order_reponse = OrderResponse(id=str(uuid.uuid4()), reference=args.reference)
    serializer = PickleSerializer()
    backend = LocalSQSBackend(
        host=os.environ.get("SQSHOST"), port=os.environ.get("SQSPORT")
    )

    QueuePublisher(serializer_registry, backend=backend).publish(
        "saga-updates", order_reponse
    )

    print(f"Order with reference {args.reference} sent.")
