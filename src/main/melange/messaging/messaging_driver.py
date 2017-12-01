class Message:
    def __init__(self, message_id, content, metadata):
        self.message_id = message_id
        self.content = content
        self.metadata = metadata


class MessagingDriver:
    def declare_topic(self, topic_name):
        raise NotImplementedError

    def declare_queue(self, queue_name, topic_to_bind=None, dead_letter_queue_name=None):
        raise NotImplementedError

    def retrieve_messages(self, queue):
        raise NotImplementedError

    def publish(self, content, topic):
        raise NotImplementedError

    def acknowledge(self, message):
        raise NotImplementedError
