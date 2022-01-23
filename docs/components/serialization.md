# Serialization

Serializers are the component that translate (serialize) your python objects into a
string that can be sent through the messaging infrastructure, and then
translate that string back (deserialize) to the python object.

Melange is bundled with two serializers:  a `JSONSerializer` to
serialize python dictionaries and a `PickleSerializer` that will
serialize any python object, but will only be deserializable from
another python process and it's generally regarded as unsafe).

When instantiating a publisher or a consumer you need to pass it 
the `SerializerRegistry`. Melange, upon sending or receiving messages, will
select the serializer that matches your message and serialize and
deserialize it with the help of the registry.

!!! info

    Much of the serialization implementation has been ported/inspired from the
    [Akka framework](https://doc.akka.io/docs/akka/current/serialization.html).
    It's really smart, so no need to rethink/redesign it too much!

## Configuration for the `SerializerRegistry`

For Melange to know which Serializer to use when publishing or consuming
messages, you need to supply to the `SerializerRegistry` a configuration:

``` py
registry_config = {
    "serializers": {
        "json": JsonSerializer,
        "pickle": PickleSerializer,
        "yourown": YourOwnSerializer,
    },
    "serializer_bindings": {
        Dict: "json",
        YourOwnMessage: "yourown",
    },
    "default": "pickle",
}
```

This config has three sections:

1. `serializers`: This is where you specify what serializers are available in the registry,
      and by what names are they bound to.
 
2. `serializer_bindings`: This is where you wire which classes should be serialized using
     which `Serializer`. You only need to specify the name of the abstract class of the messages.
     In the case of multiple serializers matching your message, the most specific configured
     class will be used. 
    
3. `default`: Optional. The default serializer to use if none matches your `serializer_bindings` mapping.
     

With this config in place, you can then instantiate the `SerializerRegistry`
and pass it to your publishers and consumer dispatchers:

``` py
registry_config = {
    "serializers": {
        "json": JsonSerializer,
        "pickle": PickleSerializer,
        "yourown": YourOwnSerializer,
    },
    "serializer_bindings": {
        Dict: "json",
        YourOwnMessage: "yourown",
    },
    "default": "pickle",
}

registry = SerializerRegistry(registry_config)

# The backend should be passed as well, ignored in this snippet
publisher = QueuePublisher(registry, backend)
```

## Creating your own serializers

To create your own serializer, you need to inherit
`Serializer` and implement the methods `identify`, `manifest`, `deserialize`
and `serialize`.

Example:

``` py
--8<-- "melange/doc_examples/serializer_example.py"
```

Constraints:

* The `identifier` must be unique, since it is used to select the serializer
that must be used for deserialization (each message that is sent through the
  `MessagingBackend` embeds this identifier, together with the content and the manifest)

Some ideas of custom serializers:

* A protocol buffer serializer: Protocol Buffers (or protobuf for short)
is a fast and compact serializing technology. In some projects where Melange
  is used in production such serializer has been implemented successfully.
