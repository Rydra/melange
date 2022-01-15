import os
import uuid

from melange.drivers.aws.elasticmq import ElasticMQDriver
from melange.examples.common.serializer import PickleSerializer
from melange.examples.payment_service.events import OrderResponse
from melange.exchange_message_publisher import SQSPublisher

if __name__ == "__main__":
    order_reponse = OrderResponse(id=str(uuid.uuid4()), reference="MYREF888888")
    serializer = PickleSerializer()
    driver = ElasticMQDriver(
        host=os.environ.get("SQSHOST"), port=os.environ.get("SQSPORT")
    )

    SQSPublisher("payment-updates", serializer, driver=driver).publish(order_reponse)

    print("Message sent.")
