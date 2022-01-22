import json
import os
import time
import uuid

import pytest
from hamcrest import *

from melange.backends.sqs.localsqs import LocalSQSBackend
from melange.models import Message


@pytest.fixture
def backend():
    return LocalSQSBackend(
        wait_time_seconds=1,
        visibility_timeout=10,
        host=os.environ.get("SQSHOST") or "http://localhost",
        port=os.environ.get("SQSPORT") or 4566,
        sns_host=os.environ.get("SNSHOST") or "http://localhost",
        sns_port=os.environ.get("SNSPORT") or 4566,
    )


@pytest.fixture
def topic(backend):
    topic = backend.declare_topic("dev-topic-{}".format(uuid.uuid4()))
    yield topic
    backend.delete_topic(topic)


def test_create_fifo_queue(backend, request):
    def delete_queue():
        backend.delete_queue(queue)

    request.addfinalizer(delete_queue)

    queue_name = "test-queue-{}.fifo".format(uuid.uuid4())
    backend.declare_queue(queue_name)
    queue = backend.get_queue(queue_name)

    assert_that(
        queue.unwrapped_obj.attributes,
        has_entries(FifoQueue="true", ContentBasedDeduplication="true"),
    )


def test_create_fifo_queue_with_dlq(backend, request):
    def delete_queue():
        backend.delete_queue(queue)
        backend.delete_queue(dlq)

    request.addfinalizer(delete_queue)

    queue_name = "test-queue-{}.fifo".format(uuid.uuid4())
    dlq_queue_name = "test-queue-{}-dlq.fifo".format(uuid.uuid4())
    queue, dlq = backend.declare_queue(
        queue_name, dead_letter_queue_name=dlq_queue_name
    )

    assert_that(
        queue.unwrapped_obj.attributes,
        has_entries(FifoQueue="true", ContentBasedDeduplication="true"),
    )
    assert_that(
        dlq.unwrapped_obj.attributes,
        has_entries(FifoQueue="true", ContentBasedDeduplication="true"),
    )


def test_create_a_non_fifo_queue(backend, request):
    def delete_queue():
        backend.delete_queue(queue)

    request.addfinalizer(delete_queue)

    queue_name = "test-queue-{}".format(uuid.uuid4())
    backend.declare_queue(queue_name)
    queue = backend.get_queue(queue_name)

    assert_that(
        queue.unwrapped_obj.attributes,
        not_(has_entries(FifoQueue="true", ContentBasedDeduplication="true")),
    )


def test_create_normal_queue_with_dlq(backend, request):
    def delete_queue():
        backend.delete_queue(queue)
        backend.delete_queue(dlq)

    request.addfinalizer(delete_queue)

    queue_name = "test-queue-{}".format(uuid.uuid4())
    dlq_queue_name = "test-queue-{}-dlq".format(uuid.uuid4())
    queue, dlq = backend.declare_queue(
        queue_name, dead_letter_queue_name=dlq_queue_name
    )

    assert_that(
        queue.unwrapped_obj.attributes,
        not_(has_entries(FifoQueue="true", ContentBasedDeduplication="true")),
    )
    assert_that(
        dlq.unwrapped_obj.attributes,
        not_(has_entries(FifoQueue="true", ContentBasedDeduplication="true")),
    )


def test_send_messages_through_a_fifo_queue_and_make_sure_they_are_always_ordered(
    backend, request
):
    def delete_queue():
        backend.delete_queue(queue)

    request.addfinalizer(delete_queue)

    queue_name = "test-queue-{}.fifo".format(uuid.uuid4())
    queue, _ = backend.declare_queue(queue_name)

    message_group_id = "my-app"

    for i in range(100):
        message_dedup_id = str(uuid.uuid4())
        backend.publish_to_queue(
            Message.create(f"my-message-{i}", "my-event-type"),
            queue,
            message_group_id=message_group_id,
            message_deduplication_id=message_dedup_id,
        )

    received_messages = []
    retrieved_messages = backend.retrieve_messages(queue)

    while retrieved_messages:
        for m in retrieved_messages:
            received_messages.append(m.content)
            backend.acknowledge(m)

        retrieved_messages = backend.retrieve_messages(queue)

    expected_array = [f"my-message-{i}" for i in range(100)]
    assert_that(received_messages, contains_exactly(*expected_array))


@pytest.mark.skip(reason="slow")
def test_not_acknowledging_any_of_the_messages_on_a_fifo_queue_will_delay_the_delivery_of_the_rest(
    backend, request
):
    def delete_queue():
        backend.delete_queue(queue)

    request.addfinalizer(delete_queue)

    queue_name = "test-queue-{}.fifo".format(uuid.uuid4())
    queue, _ = backend.declare_queue(queue_name)

    message_group_id = "my-app"

    for i in range(20):
        message_dedup_id = str(uuid.uuid4())
        backend.publish_to_queue(
            Message.create(f"my-message-{i}", "my-event-type"),
            queue,
            message_group_id=message_group_id,
            message_deduplication_id=message_dedup_id,
        )

    received_messages = []
    retrieved_messages = backend.retrieve_messages(queue)

    num_acks = 0
    while num_acks < 20:
        for i, m in enumerate(retrieved_messages):
            if i == 5:
                break
            else:
                received_messages.append(m.content)
                backend.acknowledge(m)
                num_acks += 1
        retrieved_messages = backend.retrieve_messages(queue)

    expected_array = [f"my-message-{i}" for i in range(20)]
    assert_that(received_messages, contains_exactly(*expected_array))


def test_send_messages_through_a_non_fifo_queue_does_not_guarantee_order(
    backend, request
):
    def delete_queue():
        backend.delete_queue(queue)

    request.addfinalizer(delete_queue)

    queue_name = "test-queue-{}".format(uuid.uuid4())
    queue, _ = backend.declare_queue(queue_name)

    for i in range(100):
        backend.publish_to_queue(
            Message.create(f"my-message-{i}", "my-event-type"), queue
        )

    received_messages = []
    retrieved_messages = backend.retrieve_messages(queue)

    while retrieved_messages:
        for m in retrieved_messages:
            received_messages.append(m.content)
            backend.acknowledge(m)

        retrieved_messages = backend.retrieve_messages(queue)

    expected_array = [f"my-message-{i}" for i in range(100)]
    assert_that(received_messages, contains_inanyorder(*expected_array))


def test_backend_declare_a_queue_for_a_topic_filtering_the_events_it_sends_to_certain_queues(
    backend, topic
):
    try:
        queue_1, _ = backend.declare_queue(
            "dev-queue-{}".format(uuid.uuid4()), topic, filter_events=["MyBananaEvent"]
        )
        queue_2, _ = backend.declare_queue(
            "dev-queue-{}".format(uuid.uuid4()),
            topic,
            filter_events=["MyNonBananaEvent"],
        )
        queue_3, _ = backend.declare_queue("dev-queue-{}".format(uuid.uuid4()), topic)

        backend.publish_to_topic(
            Message.create(
                json.dumps({"event_type_name": "MyBananaEvent", "value": 3}),
                "MyBananaEvent",
            ),
            topic,
        )
        backend.publish_to_topic(
            Message.create(
                json.dumps({"event_type_name": "MyNonBananaEvent", "value": 5}),
                "MyNonBananaEvent",
            ),
            topic,
        )
        time.sleep(2)

        _assert_messages(backend, queue_3, ["MyNonBananaEvent", "MyBananaEvent"], 2)
        _assert_messages(backend, queue_1, ["MyBananaEvent"], 1)
        _assert_messages(backend, queue_2, ["MyNonBananaEvent"], 1)

    finally:
        backend.delete_queue(queue_1)
        backend.delete_queue(queue_2)
        backend.delete_queue(queue_3)


def _assert_messages(backend, queue, expected_types_contained, expected_num_messages):
    messages = []
    while True:
        retrieved_messages = backend.retrieve_messages(queue)
        messages += retrieved_messages
        if len(messages) > expected_num_messages:
            raise Exception("The test has failed")
        if not retrieved_messages:
            break

    assert expected_num_messages == len(messages)

    received_event_types = [message.manifest for message in messages]
    for type in expected_types_contained:
        assert type in received_event_types
