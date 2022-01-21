import os
import uuid

from melange.backends.sqs.elasticmq import LocalSQSBackend
from melange.examples.payment_service.events import OrderResponse
from melange.publishers import QueuePublisher
from melange.serializers.pickle import PickleSerializer

if __name__ == "__main__":
    order_reponse = OrderResponse(id=str(uuid.uuid4()), reference="MYREF888888")
    serializer = PickleSerializer()
    backend = LocalSQSBackend(
        host=os.environ.get("SQSHOST"), port=os.environ.get("SQSPORT")
    )

    QueuePublisher(serializer, backend=backend).publish(
        "payment-updates", order_reponse
    )

    print("Message sent.")
