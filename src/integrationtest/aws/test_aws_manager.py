import json
import uuid

from melange.aws.aws_manager import AWSManager


class TestAWSManager:

    def setup_method(self):
        self.topic = None
        self.queue = None
        self.dead_letter_queue = None

    def teardown_method(self):
        if self.topic:
            self.topic.delete()

        if self.queue:
            self.queue.delete()

        if self.dead_letter_queue:
            self.dead_letter_queue.delete()

    def test_create_topic(self):
        self.topic = AWSManager.declare_topic(self._get_topic_name())
        assert self.topic.arn

    def test_create_normal_queue(self):
        self.queue, _ = AWSManager.declare_queue(self._get_queue_name())
        assert self.queue.url
        assert 'Policy' not in self.queue.attributes

    def test_create_queue_and_bind_to_topic(self):
        self.topic = AWSManager.declare_topic(self._get_topic_name())
        self.queue, _ = AWSManager.declare_queue(self._get_queue_name(), self.topic)

        assert self.queue.url

        policy = json.loads(self.queue.attributes['Policy'])
        policy_topic_arn = policy['Statement'][0]['Condition']['ArnEquals']['aws:SourceArn']
        assert policy_topic_arn == self.topic.arn

    def test_create_queue_with_dead_letter_queue(self):
        self.topic = AWSManager.declare_topic(self._get_topic_name())
        self.queue, self.dead_letter_queue = AWSManager.declare_queue(self._get_queue_name(),
                                                         self.topic,
                                                         dead_letter_queue_name=self._get_queue_name())

        assert self.queue.url

        attrs = self.queue.attributes

        policy = json.loads(attrs['Policy'])
        policy_topic_arn = policy['Statement'][0]['Condition']['ArnEquals']['aws:SourceArn']
        assert policy_topic_arn == self.topic.arn

        redrive_policy = json.loads(attrs['RedrivePolicy'])
        queue_arn = self.dead_letter_queue.attributes['QueueArn']

        assert redrive_policy['deadLetterTargetArn'] == queue_arn
        assert redrive_policy['maxReceiveCount'] == 4

    def _get_queue_name(self):
        return 'test_queue_{}'.format(uuid.uuid4())

    def _get_topic_name(self):
        return 'test_queue_{}'.format(uuid.uuid4())
