# Behind the scenes

## How are messages serialized

Messages, when serialized, they have the shape of a string. Some serializing formats 
might not require anything more that the message itself (like pickle). 
The message itself contains headers of some kind that tells deserializers
how they have to deserialize that message (assuming you already know you
always have to use that specific serializer). Other formats (like protobuf)
require some kind of specification that tells the consumers how the message
needs to be deserialized.

This is why *manifests* exist and are necessary. A manifest tells the aplicacion which shape
(manifestation) an array of bytes or a string had. This way we can appropriately
choose the serializer that is able to properly deserialize the message.

Imagine we want to serialize an object with a serializer that performs encryption as well:

``` py
@dataclass
class ProductCreated:
    id: int
    name: str
    
event = ProductCreated(1, "Banana")
serialzer = MyCryptographicSerializer()
serialized_event = serializer.serialize(event)
# Let's say `serialized_event` has this content:
# a&/(67567ulmtensr/((&/...29747JJJ
```

If we just sent that string to an outsider, how does it know that is a `ProductCreated`
which has been serialized with a special serializer?

However, with the aid of the manifest, we can give some clue to the
deserializer on how that message was serialized:

``` py
@dataclass
class ProductCreated:
    id: int
    name: str
    
event = ProductCreated(1, "Banana")
serialzer = MyCryptographicSerializer()
serialized_event = serializer.serialize(event)
# Let's say `serialized_event` has this content:
# a&/(67567ulmtensr/((&/...29747JJJ
manifest = serializer.manifest(event)
# manifest could be something like `mycryptoserializer:sha1:ProductCreated`
```

That way we tell the consumer who has to deserialize the message that
the message was serialized with the `MyCryptographicSerializer`, with a `SHA1`
algorithm, and that it is a `ProductCreated` event. The publishers, when
sending the message, they send the manifest as well as the serialized message
to provide the consumers with this valuable information. The manifest
could be sent through the means of metadata (if your messaging infrastructure
supports it) or through any other means that could be retrieved by the consumer.

