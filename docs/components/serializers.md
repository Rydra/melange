# Serializers

Serializers are the component that translates (serializes) your python objects into a
string that can be sent through the messaging infrastructure, and then
translates it (deserializes) that string back to the python object.

Melange is bundled with two serializers: a `JSONSerializer` to
serialize python dictionaries and a `PickleSerializer` that will
serialize any python object, but will only be deserializable from
another python process and it's generally regarded as unsafe).

When instantiating a publisher or a consumer you need to pass a list
of serializers. Melange, upon sending or receiving messages, will
select the serializer that best matches the one that can serialize and
deserialize it.

TODO: Implement the serializer selector from a list

## Creating your own serializers

To create your own serializer, you need to inherit the class
`MessageSerializer` and implement the methods `manifest`, `deserialize`
and `serialize`.

This is the `MessageSerializer` interface:

::: melange.serializers.interfaces

Some ideas of custom serializers:

* A protocol buffer serializer: Protocol Buffers (or protobuf for short)
is a fast and compact serializing technology. In some projects where Melange
  is used in production such serializer has been implemented successfully.
