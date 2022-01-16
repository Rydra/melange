import uuid

from melange.backends.rabbitmq.rabbitmq_backend import RabbitMQBackend


class TestRabbitMQBackend:
    def setup_method(self):
        self.topic = None
        self.queue = None
        self.dead_letter_queue = None

        self.backend = RabbitMQBackend(host="localhost")

    def teardown_method(self):
        if self.topic:
            self.backend.channel.exchange_delete(exchange=self.topic)

        if self.queue:
            self.backend.channel.queue_delete(queue=self.queue)

        if self.dead_letter_queue:
            self.dead_letter_queue.delete()

    def test_create_topic(self):
        topic_name = self._get_topic_name()
        self.topic = self.backend.declare_topic(topic_name)
        assert self.topic == topic_name

    def test_create_normal_queue(self):
        queue_name = self._get_queue_name()
        self.queue, _ = self.backend.declare_queue(queue_name)
        assert self.queue == queue_name

    def test_create_queue_and_bind_to_topic(self):
        self.topic = self.backend.declare_topic(self._get_topic_name())
        queue_name = self._get_queue_name()
        self.queue, _ = self.backend.declare_queue(queue_name, self.topic)

        assert self.queue == queue_name

    def _get_queue_name(self):
        return "test_queue_{}".format(uuid.uuid4())

    def _get_topic_name(self):
        return "test_queue_{}".format(uuid.uuid4())
