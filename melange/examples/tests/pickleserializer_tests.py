import uuid

from hamcrest import *

from melange.examples.payment_service.events import OrderResponse
from melange.serializers.pickle import PickleSerializer


def test_pickle_a_domain_event():
    event = OrderResponse(str(uuid.uuid4()), "REF88888")

    serializer = PickleSerializer()
    data = serializer.serialize(event)
    event = serializer.deserialize(data, manifest=None)
    assert_that(event, is_(OrderResponse))
