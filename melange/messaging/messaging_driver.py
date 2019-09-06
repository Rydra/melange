import weakref


class Message:
    def __init__(self, message_id, content, metadata):
        self.message_id = message_id
        self.content = content
        self.metadata = metadata


class MessagingDriver:
    def __init__(self):
        self._finalizer = weakref.finalize(self, self.close_connection)

    def declare_topic(self, topic_name):
        """
        Declares a topic exchange with the name "topic name" and
        returns an object that represent the topic

        :param topic_name: The name of the topic to create
        :return: An object that represents a topic. The type of the object
        is only relevant inside the context of the driver, so what you
        return as a topic will be passed in next calls to the driver
        where a topic is required
        """
        raise NotImplementedError

    def get_queue(self, queue_name):
        raise NotImplementedError

    def declare_queue(self, queue_name, *topics_to_bind, dead_letter_queue_name=None, **kwargs):
        """
        Declares a queue with the name "queue_name". Optionally, this
         queue may be binded to the topic "topic_to_bind" and associated
         to a dead_letter_queue "dead_letter_queue_name" where messages that
         were unable to deliver will be placed.

        :param queue_name: The name of the queue to create
        :param topic_to_bind: The topic object where you will bind your queue
        :param dead_letter_queue_name: The name of the dead letter queue to
        create and associate to the queue "queue_name"
        :return: A tuple, with the first element being the object queue
        created, and the second element is the dead letter queue object.
        The type of the queue object is only relevant inside the context of the driver, so what you
        return as a queue will be passed in next calls to the driver
        where a queue is required
        """
        raise NotImplementedError

    def retrieve_messages(self, queue, attempt_id=None):
        """
        Returns a list of messages (instances of Message type) that have
        been received from the queue.

        :param queue: queue to poll
        :return: a list of messages to process
        """
        raise NotImplementedError

    def publish(self, content, topic, event_type_name):
        """
        Publishes the content to the topic. The content must be a
        string (which is the json representation of an event)
        """
        raise NotImplementedError

    def queue_publish(
            self, content, queue, event_type_name,
            message_group_id=None, message_deduplication_id=None):
        raise NotImplementedError

    def acknowledge(self, message):
        """
        Acknowledges a message so that it won't be redelivered by
        the messaging infrastructure in the future
        """
        raise NotImplementedError

    def close_connection(self):
        """
        Override this function if you want to use some finalizer code
         to shutdown your driver in a clean way
        """
        pass

    def delete_queue(self, queue):
        """
        Deletes the queue
        """
        raise NotImplementedError

    def delete_topic(self, topic):
        """
        Deletes the topic
        """
        raise NotImplementedError
