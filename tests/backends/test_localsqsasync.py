import json
import os
import time
import uuid

import funcy
import pytest
from anyio import from_thread
from hamcrest import *

from melange.backends.interfaces import AsyncMessagingBackend
from melange.backends.sqs.sqs_backend_async import AsyncLocalSQSBackend
from melange.models import Message, MessageDto


@pytest.fixture
def backend():
    return AsyncLocalSQSBackend(
        wait_time_seconds=1,
        visibility_timeout=10,
        host=os.environ.get("SQSHOST") or "http://localhost",
        port=os.environ.get("SQSPORT") or 4566,
        sns_host=os.environ.get("SNSHOST") or "http://localhost",
        sns_port=os.environ.get("SNSPORT") or 4566,
    )


@pytest.fixture
async def topic(backend: AsyncMessagingBackend):
    topic = await backend.declare_topic("dev-topic-{}".format(uuid.uuid4()))
    yield topic
    await backend.delete_topic(topic)


async def test_create_fifo_queue(
    backend: AsyncMessagingBackend, request, anyio_backend
):
    def delete_queue():
        # Queue deletion is asynchronous, but the request tear down is not...
        with from_thread.start_blocking_portal(backend="asyncio") as portal:
            portal.start_task_soon(backend.delete_queue, queue)

    request.addfinalizer(delete_queue)

    queue_name = "test-queue-{}.fifo".format(uuid.uuid4())
    await backend.declare_queue(queue_name)
    queue = await backend.get_queue(queue_name)

    # I need to wrap this into some kind of aioboto session, otherwise getting
    # the attribute raises an HTTP error
    attributes = await backend.get_queue_attributes(queue)
    assert_that(
        attributes,
        has_entries(FifoQueue="true", ContentBasedDeduplication="true"),
    )


async def test_create_fifo_queue_with_dlq(
    backend: AsyncMessagingBackend, request, anyio_backend
):
    def delete_queue():
        # Queue deletion is asynchronous, but the request tear down is not...
        with from_thread.start_blocking_portal(backend="asyncio") as portal:
            portal.start_task_soon(backend.delete_queue, queue)
            portal.start_task_soon(backend.delete_queue, dlq)

    request.addfinalizer(delete_queue)

    queue_name = "test-queue-{}.fifo".format(uuid.uuid4())
    dlq_queue_name = "test-queue-{}-dlq.fifo".format(uuid.uuid4())
    queue, dlq = await backend.declare_queue(
        queue_name, dead_letter_queue_name=dlq_queue_name
    )

    attr = await backend.get_queue_attributes(queue)
    assert_that(
        attr,
        has_entries(FifoQueue="true", ContentBasedDeduplication="true"),
    )
    attr = await backend.get_queue_attributes(dlq)
    assert_that(
        attr,
        has_entries(FifoQueue="true", ContentBasedDeduplication="true"),
    )


async def test_create_a_non_fifo_queue(
    backend: AsyncMessagingBackend, request, anyio_backend
):
    def delete_queue():
        with from_thread.start_blocking_portal(backend="asyncio") as portal:
            portal.start_task_soon(backend.delete_queue, queue)

    request.addfinalizer(delete_queue)

    queue_name = "test-queue-{}".format(uuid.uuid4())
    queue, _ = await backend.declare_queue(queue_name)
    attributes = await backend.get_queue_attributes(queue)

    assert_that(
        attributes,
        not_(has_entries(FifoQueue="true", ContentBasedDeduplication="true")),
    )


async def test_create_normal_queue_with_dlq(
    backend: AsyncMessagingBackend, request, anyio_backend
):
    def delete_queue():
        with from_thread.start_blocking_portal(backend="asyncio") as portal:
            portal.start_task_soon(backend.delete_queue, queue)
            portal.start_task_soon(backend.delete_queue, dlq)

    request.addfinalizer(delete_queue)

    queue_name = "test-queue-{}".format(uuid.uuid4())
    dlq_queue_name = "test-queue-{}-dlq".format(uuid.uuid4())
    queue, dlq = await backend.declare_queue(
        queue_name, dead_letter_queue_name=dlq_queue_name
    )

    attr = await backend.get_queue_attributes(queue)
    assert_that(
        attr,
        not_(has_entries(FifoQueue="true", ContentBasedDeduplication="true")),
    )

    attr = await backend.get_queue_attributes(dlq)
    assert_that(
        attr,
        not_(has_entries(FifoQueue="true", ContentBasedDeduplication="true")),
    )


async def test_send_messages_through_a_fifo_queue_and_make_sure_they_are_always_ordered(
    backend: AsyncMessagingBackend, request, anyio_backend
):
    def delete_queue():
        with from_thread.start_blocking_portal(backend="asyncio") as portal:
            portal.start_task_soon(backend.delete_queue, queue)

    request.addfinalizer(delete_queue)

    queue_name = "test-queue-{}.fifo".format(uuid.uuid4())
    queue, _ = await backend.declare_queue(queue_name)

    message_group_id = "my-app"

    messages = []
    for i in range(20):
        message_dedup_id = str(uuid.uuid4())
        messages.append(
            MessageDto(
                Message.create(f"my-message-{i}", "my-event-type", 40),
                message_group_id,
                message_dedup_id,
            )
        )

    for chunk in funcy.chunks(10, messages):
        await backend.publish_to_queue_batch(chunk, queue)

    received_messages = []

    while True:
        retrieved_messages = backend.retrieve_messages(queue)
        iterated = False
        async for m in retrieved_messages:
            iterated = True
            received_messages.append(m.content)
            await backend.acknowledge(m)
        if not iterated:
            break

    expected_array = [f"my-message-{i}" for i in range(20)]
    assert_that(received_messages, contains_exactly(*expected_array))


async def test_send_messages_through_a_fifo_queue_and_make_sure_they_are_always_ordered_by_batch(
    backend: AsyncMessagingBackend, request, anyio_backend
):
    def delete_queue():
        with from_thread.start_blocking_portal(backend="asyncio") as portal:
            portal.start_task_soon(backend.delete_queue, queue)

    request.addfinalizer(delete_queue)

    queue_name = "test-queue-{}.fifo".format(uuid.uuid4())
    queue, _ = await backend.declare_queue(queue_name)

    message_group_id = "my-app"

    for i in range(20):
        message_dedup_id = str(uuid.uuid4())
        await backend.publish_to_queue(
            Message.create(f"my-message-{i}", "my-event-type", 40),
            queue,
            message_group_id=message_group_id,
            message_deduplication_id=message_dedup_id,
        )

    received_messages = []

    while True:
        retrieved_messages = backend.retrieve_messages(queue)
        iterated = False
        async for m in retrieved_messages:
            iterated = True
            received_messages.append(m.content)
            await backend.acknowledge(m)
        if not iterated:
            break

    expected_array = [f"my-message-{i}" for i in range(20)]
    assert_that(received_messages, contains_exactly(*expected_array))


@pytest.mark.skip(reason="slow")
def test_not_acknowledging_any_of_the_messages_on_a_fifo_queue_will_delay_the_delivery_of_the_rest(
    backend: AsyncMessagingBackend, request
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
            Message.create(f"my-message-{i}", "my-event-type", 40),
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


async def test_send_messages_through_a_non_fifo_queue_does_not_guarantee_order(
    backend: AsyncMessagingBackend, request, anyio_backend
):
    def delete_queue():
        with from_thread.start_blocking_portal(backend="asyncio") as portal:
            portal.start_task_soon(backend.delete_queue, queue)

    request.addfinalizer(delete_queue)

    queue_name = "test-queue-{}".format(uuid.uuid4())
    queue, _ = await backend.declare_queue(queue_name)

    await backend.publish_to_queue_batch(
        [
            MessageDto(Message.create(f"my-message-{i}", "my-event-type", 40))
            for i in range(100)
        ],
        queue,
    )

    received_messages = []
    messages_handles = []
    while True:
        messages_found = False
        async for m in backend.retrieve_messages(queue):
            messages_found = True
            received_messages.append(m.content)
            messages_handles.append(m)

        if not messages_found:
            break

    await backend.acknowledge_batch(messages_handles)

    expected_array = [f"my-message-{i}" for i in range(100)]
    assert_that(received_messages, contains_inanyorder(*expected_array))


async def test_backend_declare_a_queue_for_a_topic_filtering_the_events_it_sends_to_certain_queues(
    backend: AsyncMessagingBackend, topic, anyio_backend
):
    try:
        queue_1, _ = await backend.declare_queue(
            "dev-queue-{}".format(uuid.uuid4()), topic, filter_events=["MyBananaEvent"]
        )
        queue_2, _ = await backend.declare_queue(
            "dev-queue-{}".format(uuid.uuid4()),
            topic,
            filter_events=["MyNonBananaEvent"],
        )
        queue_3, _ = await backend.declare_queue(
            "dev-queue-{}".format(uuid.uuid4()), topic
        )

        await backend.publish_to_topic(
            Message.create(
                json.dumps({"event_type_name": "MyBananaEvent", "value": 3}),
                "MyBananaEvent",
                40,
            ),
            topic,
        )
        await backend.publish_to_topic(
            Message.create(
                json.dumps({"event_type_name": "MyNonBananaEvent", "value": 5}),
                "MyNonBananaEvent",
                40,
            ),
            topic,
        )
        time.sleep(2)

        await _assert_messages(
            backend, queue_3, ["MyNonBananaEvent", "MyBananaEvent"], 2
        )
        await _assert_messages(backend, queue_1, ["MyBananaEvent"], 1)
        await _assert_messages(backend, queue_2, ["MyNonBananaEvent"], 1)

    finally:
        await backend.delete_queue(queue_1)
        await backend.delete_queue(queue_2)
        await backend.delete_queue(queue_3)


async def _assert_messages(
    backend: AsyncMessagingBackend,
    queue,
    expected_types_contained,
    expected_num_messages,
):
    messages = []
    while True:
        retrieved_messages = backend.retrieve_messages(queue)

        new_messages = [i async for i in retrieved_messages]
        messages.extend(new_messages)
        await backend.acknowledge_batch(new_messages)
        if len(messages) > expected_num_messages:
            raise Exception("The test has failed")
        if not new_messages:
            break

    assert expected_num_messages == len(messages)

    received_event_types = [message.manifest for message in messages]
    for type in expected_types_contained:
        assert type in received_event_types
