import os

from melange.drivers.aws.elasticmq import ElasticMQDriver
from melange.examples.common.serializer import PickleSerializer
from melange.examples.payment_service.consumer import PaymentConsumer
from melange.examples.payment_service.publisher import PaymentPublisher
from melange.examples.payment_service.repository import PaymentRepository
from melange.examples.payment_service.service import PaymentService
from melange.exchange_message_consumer import ExchangeMessageConsumer
from melange.exchange_message_publisher import SQSPublisher

if __name__ == "__main__":
    serializer = PickleSerializer()
    driver = ElasticMQDriver(
        host=os.environ.get("SQSHOST"), port=os.environ.get("SQSPORT")
    )

    exchange_consumer = ExchangeMessageConsumer(
        PickleSerializer(),
        driver=driver,
    )

    payment_consumer = PaymentConsumer(
        PaymentService(
            PaymentRepository(),
            PaymentPublisher(SQSPublisher(serializer, driver=driver)),
        )
    )

    exchange_consumer.subscribe(payment_consumer)

    print("Consuming...")
    while True:
        exchange_consumer.consume_event("payment-updates")
