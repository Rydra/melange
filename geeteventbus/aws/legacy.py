#
# class MessagePublisher:
#     def __init__(self, event_serializer_map, topic):
#
#         self.event_serializer_map = event_serializer_map
#
#         self.sns = boto3.client('sns')
#
#         topic_mapper = ArnTopicMapper()
#         self.topic_arn = topic_mapper.map_topic_to_arn(topic)
#         self.keep_running = True
#
#     def publish(self, event):
#
#         if not isinstance(event, Event):
#             logging.error('Invalid data passed. You must pass an event instance')
#             return False
#         if not self.keep_running:
#             return False
#
#         response = self.sns.publish(
#             TopicArn=self.topic_arn,
#             Message=self._serialize(event))
#
#         if 'MessageId' not in response:
#             raise ConnectionError('Could not send the event to the SNS TOPIC')
#
#         return True
#
#     def _serialize(self, event):
#         event_type_name = event.event_type_name
#
#         if event_type_name not in self.event_serializer_map:
#             raise ValueError("The event type {} doesn't have a registered serializer")
#
#         schema = self.event_serializer_map[event_type_name]
#         return schema.dumps(event).data
#
#
# class MessageConsumer:
#     def __init__(self, event_serializer_map, queue_name):
#         # TODO: This map must be easily configurable. Think of a better way!
#         self.event_serializer_map = event_serializer_map
#
#         register(self.shutdown)
#         self.consumers = {}
#
#         sqs = boto3.resource('sqs')
#         self.event_queue = sqs.get_queue_by_name(QueueName=queue_name)
#
#         self.keep_running = True
#         self.stop_time = 0
#         self.shutdown_lock = Lock()
#
#         name = 'executor_thread_main'
#         self.event_thread = Thread(target=self, name=name)
#         self.event_thread.start()
#
#     def register_consumer(self, consumer):
#
#         if not isinstance(consumer, subscriber):
#             return False
#
#         listened_event_type_name = consumer.listens_to()
#
#         if listened_event_type_name not in self.consumers:
#             self.consumers[listened_event_type_name] = []
#
#         self.consumers[listened_event_type_name].append(consumer)
#
#     def unregister_consumer(self, consumer):
#
#         listened_event_type_name = consumer.listens_to()
#
#         if listened_event_type_name in self.consumers and consumer in self.consumers[listened_event_type_name]:
#             self.consumers[listened_event_type_name].remove(consumer)
#
#             if len(self.consumers[listened_event_type_name]) == 0:
#                 del self.consumers[listened_event_type_name]
#
#     def __call__(self):
#
#         while not self._thread_should_end():
#             eventobj = self._get_next_event()
#             if eventobj is not None:
#                 self._process_event(eventobj)
#
#     def _deserialize(self, event_dict):
#         event_type_name = event_dict['event_type_name']
#
#         if event_type_name not in self.event_serializer_map:
#             raise ValueError("The event type {} doesn't have a registered serializer")
#
#         schema = self.event_serializer_map[event_type_name]
#         return schema.load(event_dict).data
#
#     def _get_subscribers(self, event_type_name):
#         return self.consumers[event_type_name] if event_type_name in self.consumers else []
#
#     def _get_next_event(self):
#
#         messages = self.event_queue.receive_messages(MaxNumberOfMessages=1, VisibilityTimeout=100,
#                                                      WaitTimeSeconds=10)
#
#         try:
#             for message in messages:
#                 body = message.body
#                 message.delete()
#                 message_content = json.loads(body)
#
#                 if 'Message' in message_content:
#                     content = json.loads(message_content['Message'])
#                 else:
#                     content = message_content
#
#                 if 'event_type_name' in content:
#                     return self._deserialize(content)
#                 else:
#                     raise Exception("No event_type_name")
#
#         except Empty:
#             return None
#         except Exception as e:
#             logging.error(e)
#             return None
#
#     def _process_event(self, eventobj):
#         for subscr in self._get_subscribers(eventobj.event_type_name):
#
#             try:
#                 subscr.process(eventobj)
#             except Exception as e:
#                 logging.error(e)
#
#     def _thread_should_end(self):
#         return 0 < self.stop_time < time()
#
#     def shutdown(self):
#         '''
#         Stops the event bus. The event bus will stop all its executor threads.
#         It will try to flush out already queued events by calling the subscribers
#         of the events. This flush wait time is 2 seconds.
#         '''
#
#         with self.shutdown_lock:
#             if not self.keep_running:
#                 return
#             self.keep_running = False
#         self.stop_time = time() + 2
#
#         self.event_thread.join()