import uuid

from melange import RabbitMQDriver


class TestRabbitMQDriver:

    def setup_method(self):
        self.topic = None
        self.queue = None
        self.dead_letter_queue = None

        self.driver = RabbitMQDriver(host='localhost')

    def teardown_method(self):
        if self.topic:
            self.driver.channel.exchange_delete(exchange=self.topic)

        if self.queue:
            self.driver.channel.queue_delete(queue=self.queue)

        if self.dead_letter_queue:
            self.dead_letter_queue.delete()

    def test_create_topic(self):
        topic_name = self._get_topic_name()
        self.topic = self.driver.declare_topic(topic_name)
        assert self.topic == topic_name

    def test_create_normal_queue(self):
        queue_name = self._get_queue_name()
        self.queue, _ = self.driver.declare_queue(queue_name)
        assert self.queue == queue_name

    def test_create_queue_and_bind_to_topic(self):
        self.topic = self.driver.declare_topic(self._get_topic_name())
        queue_name = self._get_queue_name()
        self.queue, _ = self.driver.declare_queue(queue_name, self.topic)

        assert self.queue == queue_name

    # def test_create_queue_with_dead_letter_queue(self):
    #     self.topic = self.driver.declare_topic(self._get_topic_name())
    #     self.queue, self.dead_letter_queue = self.driver.declare_queue(self._get_queue_name(),
    #                                                      self.topic,
    #                                                      dead_letter_queue_name=self._get_queue_name())
    #
    #     assert self.queue.url
    #
    #     attrs = self.queue.attributes
    #
    #     policy = json.loads(attrs['Policy'])
    #     policy_topic_arn = policy['Statement'][0]['Condition']['ArnEquals']['aws:SourceArn']
    #     assert policy_topic_arn == self.topic.arn
    #
    #     redrive_policy = json.loads(attrs['RedrivePolicy'])
    #     queue_arn = self.dead_letter_queue.attributes['QueueArn']
    #
    #     assert redrive_policy['deadLetterTargetArn'] == queue_arn
    #     assert redrive_policy['maxReceiveCount'] == 4

    def _get_queue_name(self):
        return 'test_queue_{}'.format(uuid.uuid4())

    def _get_topic_name(self):
        return 'test_queue_{}'.format(uuid.uuid4())
