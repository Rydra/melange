import os
import uuid

from melange.backends.sqs.elasticmq import ElasticMQBackend
from melange.examples.common.serializer import PickleSerializer
from melange.examples.payment_service.events import OrderResponse
from melange.message_publisher import QueuePublisher

if __name__ == "__main__":
    order_reponse = OrderResponse(id=str(uuid.uuid4()), reference="MYREF888888")
    serializer = PickleSerializer()
    backend = ElasticMQBackend(
        host=os.environ.get("SQSHOST"), port=os.environ.get("SQSPORT")
    )

    QueuePublisher(serializer, backend=backend).publish(
        "payment-updates", order_reponse
    )

    print("Message sent.")
