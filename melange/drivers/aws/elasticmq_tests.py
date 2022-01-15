import json
import os
import time
import uuid

import pytest
from hamcrest import *

from melange.drivers.aws.elasticmq import ElasticMQDriver


@pytest.fixture
def driver():
    return ElasticMQDriver(
        wait_time_seconds=1,
        visibility_timeout=10,
        host=os.environ.get("SQSHOST"),
        port=os.environ.get("SQSPORT"),
    )


@pytest.fixture
def topic(driver):
    topic = driver.declare_topic("dev-topic-{}".format(uuid.uuid4()))
    yield topic
    driver.delete_topic(topic)


def test_create_fifo_queue(driver, request):
    def delete_queue():
        driver.delete_queue(queue)

    request.addfinalizer(delete_queue)

    queue_name = "test-queue-{}.fifo".format(uuid.uuid4())
    driver.declare_queue(queue_name)
    queue = driver.get_queue(queue_name)

    assert_that(
        queue.attributes,
        has_entries(FifoQueue="true", ContentBasedDeduplication="true"),
    )


def test_create_fifo_queue_with_dlq(driver, request):
    def delete_queue():
        driver.delete_queue(queue)
        driver.delete_queue(dlq)

    request.addfinalizer(delete_queue)

    queue_name = "test-queue-{}.fifo".format(uuid.uuid4())
    dlq_queue_name = "test-queue-{}-dlq.fifo".format(uuid.uuid4())
    queue, dlq = driver.declare_queue(queue_name, dead_letter_queue_name=dlq_queue_name)

    assert_that(
        queue.attributes,
        has_entries(FifoQueue="true", ContentBasedDeduplication="true"),
    )
    assert_that(
        dlq.attributes, has_entries(FifoQueue="true", ContentBasedDeduplication="true")
    )


def test_create_a_non_fifo_queue(driver, request):
    def delete_queue():
        driver.delete_queue(queue)

    request.addfinalizer(delete_queue)

    queue_name = "test-queue-{}".format(uuid.uuid4())
    driver.declare_queue(queue_name)
    queue = driver.get_queue(queue_name)

    assert_that(
        queue.attributes,
        not_(has_entries(FifoQueue="true", ContentBasedDeduplication="true")),
    )


def test_create_normal_queue_with_dlq(driver, request):
    def delete_queue():
        driver.delete_queue(queue)
        driver.delete_queue(dlq)

    request.addfinalizer(delete_queue)

    queue_name = "test-queue-{}".format(uuid.uuid4())
    dlq_queue_name = "test-queue-{}-dlq".format(uuid.uuid4())
    queue, dlq = driver.declare_queue(queue_name, dead_letter_queue_name=dlq_queue_name)

    assert_that(
        queue.attributes,
        not_(has_entries(FifoQueue="true", ContentBasedDeduplication="true")),
    )
    assert_that(
        dlq.attributes,
        not_(has_entries(FifoQueue="true", ContentBasedDeduplication="true")),
    )


def test_send_messages_through_a_fifo_queue_and_make_sure_they_are_always_ordered(
    driver, request
):
    def delete_queue():
        driver.delete_queue(queue)

    request.addfinalizer(delete_queue)

    queue_name = "test-queue-{}.fifo".format(uuid.uuid4())
    queue, _ = driver.declare_queue(queue_name)

    message_group_id = "my-app"

    for i in range(100):
        message_dedup_id = str(uuid.uuid4())
        driver.queue_publish(
            f"my-message-{i}",
            queue,
            "my-event-type",
            message_group_id,
            message_dedup_id,
        )

    received_messages = []
    retrieved_messages = driver.retrieve_messages(queue)

    while retrieved_messages:
        for m in retrieved_messages:
            received_messages.append(m.content)
            driver.acknowledge(m)

        retrieved_messages = driver.retrieve_messages(queue)

    expected_array = [f"my-message-{i}" for i in range(100)]
    assert_that(received_messages, contains(*expected_array))


def test_not_acknowledging_any_of_the_messages_on_a_fifo_queue_will_delay_the_delivery_of_the_rest(
    driver, request
):
    def delete_queue():
        driver.delete_queue(queue)

    request.addfinalizer(delete_queue)

    queue_name = "test-queue-{}.fifo".format(uuid.uuid4())
    queue, _ = driver.declare_queue(queue_name)

    message_group_id = "my-app"

    for i in range(20):
        message_dedup_id = str(uuid.uuid4())
        driver.queue_publish(
            f"my-message-{i}",
            queue,
            "my-event-type",
            message_group_id,
            message_dedup_id,
        )

    received_messages = []
    retrieved_messages = driver.retrieve_messages(queue)

    num_acks = 0
    while num_acks < 20:
        for i, m in enumerate(retrieved_messages):
            if i == 5:
                break
            else:
                received_messages.append(m.content)
                driver.acknowledge(m)
                num_acks += 1
        retrieved_messages = driver.retrieve_messages(queue)

    expected_array = [f"my-message-{i}" for i in range(20)]
    assert_that(received_messages, contains(*expected_array))


def test_send_messages_through_a_non_fifo_queue_does_not_guarantee_order(
    driver, request
):
    def delete_queue():
        driver.delete_queue(queue)

    request.addfinalizer(delete_queue)

    queue_name = "test-queue-{}".format(uuid.uuid4())
    queue, _ = driver.declare_queue(queue_name)

    for i in range(100):
        driver.queue_publish(f"my-message-{i}", queue, "my-event-type")

    received_messages = []
    retrieved_messages = driver.retrieve_messages(queue)

    while retrieved_messages:
        for m in retrieved_messages:
            received_messages.append(m.content)
            driver.acknowledge(m)

        retrieved_messages = driver.retrieve_messages(queue)

    expected_array = [f"my-message-{i}" for i in range(100)]
    assert_that(received_messages, not_(contains(*expected_array)))
    assert_that(received_messages, contains_inanyorder(*expected_array))


def test_driver_declare_a_queue_for_a_topic_filtering_the_events_it_sends_to_certain_queues(
    driver, topic
):
    try:
        queue_1, _ = driver.declare_queue(
            "dev-queue-{}".format(uuid.uuid4()), topic, filter_events=["MyBananaEvent"]
        )
        queue_2, _ = driver.declare_queue(
            "dev-queue-{}".format(uuid.uuid4()),
            topic,
            filter_events=["MyNonBananaEvent"],
        )
        queue_3, _ = driver.declare_queue("dev-queue-{}".format(uuid.uuid4()), topic)

        driver.publish(
            json.dumps({"event_type_name": "MyBananaEvent", "value": 3}),
            topic,
            event_type_name="MyBananaEvent",
        )
        driver.publish(
            json.dumps({"event_type_name": "MyNonBananaEvent", "value": 5}),
            topic,
            event_type_name="MyNonBananaEvent",
        )
        time.sleep(2)

        _assert_messages(driver, queue_3, ["MyNonBananaEvent", "MyBananaEvent"], 2)
        _assert_messages(driver, queue_1, ["MyBananaEvent"], 1)
        _assert_messages(driver, queue_2, ["MyNonBananaEvent"], 1)

    finally:
        driver.delete_queue(queue_1)
        driver.delete_queue(queue_2)
        driver.delete_queue(queue_3)


def _assert_messages(driver, queue, expected_types_contained, expected_num_messages):
    messages = []
    while True:
        retrieved_messages = driver.retrieve_messages(queue)
        messages += retrieved_messages
        if len(messages) > expected_num_messages:
            raise Exception("The test has failed")
        if not retrieved_messages:
            break

    assert expected_num_messages == len(messages)

    received_event_types = [message.content["event_type_name"] for message in messages]
    for type in expected_types_contained:
        assert type in received_event_types
