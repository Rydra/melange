import json
import time
import uuid

import pytest

from melange import AWSDriver

@pytest.fixture
def aws_driver():
    return AWSDriver(wait_time_seconds=1)

@pytest.fixture
def topic(aws_driver):
    topic = aws_driver.declare_topic('dev-topic-{}'.format(uuid.uuid4()))
    yield topic
    aws_driver.delete_topic(topic)


def test_aws_driver_declare_a_queue_for_a_topic_filtering_the_events_it_sends_to_certain_queues(aws_driver, topic):
    try:
        queue_1, _ = aws_driver.declare_queue('dev-queue-{}'.format(uuid.uuid4()), topic, filter_events=['MyBananaEvent'])
        queue_2, _ = aws_driver.declare_queue('dev-queue-{}'.format(uuid.uuid4()), topic, filter_events=['MyNonBananaEvent'])
        queue_3, _ = aws_driver.declare_queue('dev-queue-{}'.format(uuid.uuid4()), topic)

        aws_driver.publish(json.dumps({'event_type_name': 'MyBananaEvent', 'value': 3}), topic, event_type_name='MyBananaEvent')
        aws_driver.publish(json.dumps({'event_type_name': 'MyNonBananaEvent', 'value': 5}), topic, event_type_name='MyNonBananaEvent')
        time.sleep(2)

        _assert_messages(aws_driver, queue_3, ['MyNonBananaEvent', 'MyBananaEvent'], 2)
        _assert_messages(aws_driver, queue_1, ['MyBananaEvent'], 1)
        _assert_messages(aws_driver, queue_2, ['MyNonBananaEvent'], 1)

    finally:
        aws_driver.delete_queue(queue_1)
        aws_driver.delete_queue(queue_2)
        aws_driver.delete_queue(queue_3)


def _assert_messages(aws_driver, queue, expected_types_contained, expected_num_messages):
    messages = []
    while True:
        retrieved_messages = aws_driver.retrieve_messages(queue)
        messages += retrieved_messages
        if len(messages) > expected_num_messages:
            raise Exception('The test has failed')
        if not retrieved_messages: break

    assert expected_num_messages == len(messages)

    received_event_types = [message.content['event_type_name'] for message in messages]
    for type in expected_types_contained:
        assert type in received_event_types