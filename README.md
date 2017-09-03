# Melange

## An eventbus and AWS SNS+SQS message exchange for concurrent programming 

The spice must flow! (or in this case, the event)

Melange is a fork of geeteventbus and built upon its foundation to offer a flexible library 
to create distributed event-driven architectures using Amazon Web Services SNS (Simple Notification Service) 
and SQS (Simple Queue Service) as message broker. Its main selling point is the capability to greatly decouple 
and integrate REST apis, AWS Lambda functions and console applications... as long as they can subscribe to SNS 
topics. Not only that, Melange supports single-process, memory-based applications as well without depending on 
AWS services if you require it, just as geeteventbus does (Console applications, background workers). 

## Building pieces

This section describes the main classes that you basically care when working with Melange. All these 
classes only work with AWS at the time being. In addition bear in mind that you'll require an AWS account 
configured in your system (environment variables, .aws/credentials file...)

### The Event class

All events of your system MUST inherit `Event` in order to work with Melange. The event base class 
contains the two important properties, `topic`, which determine the SNS topic to where this event is sent, 
and `event_type_name` which subscribers will help subscribers determine whether they are interested in 
this kind of event or not.

Another property events have is `occurred_on` property, which is a datetime. Since it is not guaranteed 
that the events arrive in the same order you've published them, this datetime can help you to achieve 
ordering in your subscribers if you require it (as long as you track the date of the latest event received)

Example of an Event:

```python
class ExampleEvent(Event):
	event_type_name = 'ExampleEvent'
	
	def __init__(self, topic, data):
		super().__init__(topic, self.event_type_name)
		self.data = data
```
 
TODO: I'm studying whether if, instead of events, the subscribers should be the ones to determine the events 
they are interested in. To me it makes more sense.

### The Subscriber class

All subscribers must implement the `Subscriber` class and implement the process and listens_to methods. 
process contains the logic you want to execute as a reaction to a specific event being published (receiving the
published event as parameter), and the listens_to event specifies the kind of events this Subscriber is 
interested in.

Example of a subscriber:

```python
class ExampleSubscriber(Subscriber):

	def __init__(self):
		super().__init__()
		self._counter = 0
	
	def process(self, event):
		self._counter += 1
		
	def listens_to(self):
		return ExampleEvent.event_type_name
```

### The Event Serializer

The event serializer defines how your events should be serialized and deserialized when traveling through 
the messaging system. Melange uses marshmallow as serializing engine and all your event schemas should inherit 
from the EventSchema class.

When instantiating an EventSerializer, you need to supply a dictionary which acts as a map between the name 
of the event and the serialization schema to apply to that event.

You can define an schema like this:

```python
class ExampleEventSchema(EventSchema):
	data = fields.Str()
	
	@post_load
	def build(self, event_dict):
		return ExampleEvent(event_dict['topic'], event_dict['data'])
```

And then you can create the Event Serializer like this:

```python
event_serializer = EventSerializer({
	ExampleEvent.event_type_name: ExampleEventSchema(), # Do not forget to provide the instance schema, not the class
	ExampleEvent_2.event_type_name: ExampleEvent2Schema()
})
```

In a future it I plan to add functionality to bind schemas and events through their name using a convention, 
although I'm not yet experienced on how to do reflection on python to scan all the classes of your module 
looking for events and schemas. Any advice on this matter is welcome and appreciated!


### The MessagePublisher

The message publisher, as its name implies, publishes messages to an SNS topic. The name of the topic is 
contained inside the event object passed as parameter. If the topic does not exist, a new one is created 
(although the message will be lost since it won't have any subscribers...)

Here you have an example on how to instantiate and use a message publisher (you need to supply the event 
serializer as a constructor parameter so that the message publisher knows how to serialize the events):

```python
message_publisher = MessagePublisher(event_serializer)

# The event supplied in publish must be an instance of Event:
message_publisher.publish(your_event_instance)
```

### The MessageConsumer

The message consumer binds himself to a queue and allows you to consume events from it, sending the event 
to all the registered subscribers which are interested in the specific type of event.

Melange implements two types of consumers, a synchronous consumer where you manually trigger the consume 
of events in the queue, and a threaded consumer which continuously polls the queue in the background looking 
for new events and dispatching them to the registered subscribers.

Example:

```python
message_consumer = MessageConsumer(
					event_serializer, 
					event_queue_name='a_queue_name',
					topic_to_subscribe='a_topic_name')
					
message_consumer.subscribe(example_subscriber)
message_consumer.subscribe(example_subscriber2)

# Consumes an event from the queue and dispatches it to all subscribers
message_consumer.consume_event(self)
```

Threaded example:

```python
message_consumer = ThreadedMessageConsumer(
					event_serializer, 
					event_queue_name='a_queue_name',
					topic_to_subscribe='a_topic_name')
					
message_consumer.subscribe(example_subscriber)
message_consumer.subscribe(example_subscriber2)

# Events will be automatically dispatched to the subscribers
```

### The Event Bus

The event bus aims to be a single point of communication for all your events in the system. When you run 
your application, you initialize it and the EventBus will allow you to publish events which will be dispatched 
to all registered subscribers.
 
 In a nutshell, it's just the combination of the MessageConsumer and the MessagePublisher embedded in a 
 singleton that you can use in any point of your application.

Example:

```python
EventBus.init(event_serializer, 
				event_queue_name='a_queue_name',
				topic_to_subscribe='a_topic_name')
					
EventBus.get_instance().subscribe(example_subscriber)
EventBus.get_instance().subscribe(example_subscriber2)

EventBus.start()

EventBus.get_instance().publish(your_event)
```

# Use cases

### AWS Lambda functions

Melange is great to communicate with AWS Lambda functions and integrate them with other lambdas or systems. 
You could:

- Use the `MessagePublisher` to publish events to SNS topics (which then could trigger other Lambdas/systems).
- Use the `MessageConsumer` on a schedule-job based lambda to dequeue one event from an SQS queue for processing.

If the Lambda is triggered by SNS, SNS will wrap the message in a dictionary structure. You can deserialize the 
message by using the `parse_event_from_sns` function.

Example of a Lambda function code:

```python
def handle_event(message, context):

	event_serializer = EventSerializer({
		MyEvent.event_type_name: MyEventSchema(),
		MyFooCreated.event_type_name: MyFooCreatedSchema()
	})

    event = parse_event_from_sns(message, event_serializer)

	# Here you can check whether the parsed event is the one expected by your Lambda function
    if not isinstance(event, MyEvent):
        raise Exception('The passed event is not a MyEvent')

	# Your event-processing code here...
	do_work(event)
	
	# Notify
	
	event_to_publish = MyFooCreated()
	message_publisher = MessagePublisher(event_serializer)
	
	# This publish, depending on who is suscribed to the topic, will trigger other systems.
	message_publisher.publish(event_to_publish)
```

### Console Application

The `EventBus` allows you to create applications that react to events. When you initialize it, it will run a 
background thread that will poll all the SQS queues that your subscribers are interested and dispatch events 
to them.

You should include this in your initialization code:

```python
EventBus.init(event_serializer, 
				event_queue_name='a_queue_name',
				topic_to_subscribe='a_topic_name')
					
# Subscribe here all your listeners
EventBus.get_instance().subscribe(example_subscriber)
EventBus.get_instance().subscribe(example_subscriber2)

# Start the event bus
EventBus.start()

# Do further actions your app require, the event bus will do its job in the background
```

The `EventBus` polls the queues in a single thread. Possible further improvements on this library may include 
having multiple threads/processes to poll these queues, improving performance.

If you want a single-process, memory-based event bus, you could use the `AsynchronousEventBus` and 
`SynchronousEventBus`, which do not depend on any AWS service. (Pending to write proper documentation 
about them)

### Interact with Django/Flask APIs
 
SNS allows you to register endpoints on topics. You can use the `MessagePublisher` to publish messages to these 
SNS topics and SNS will send the messages to those endpoints, allowing you to seamlessly integrate your apis and 
other systems.


# Why the name 'Melange'

The name "Melange" is a reference to the drug-spice from the sci-fi book saga "Dune", a spice which is only 
generated in a single planet in the universe (planet Dune) and every human depends on it.

>If the spice flows, then the spice can be controlled.  
He who controls the spice, controls the universe.  
The spice must flow.

The analogy can be very well made on Events in a distributed architecture :)
