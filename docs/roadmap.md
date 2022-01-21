# Roadmap

## Multiple serializers

Right now, you can only supply one serializer to a publisher or a consumer,
and the same serializer will always be used for all the messages published and received. 
This could be extended to support multiple serializers, and then let 
the library choose the appropriate library to use depending on the type
of the message or the attached manifest. That way you could even implement
serializer versioning (e.g. have different versions of the same serializer)

The akka framework implements a [similar concept](https://doc.akka.io/docs/akka/current/serialization.html).

## Kombu integration

Maybe The Messaging Backends could be entirely replaced with Kombu, since kombu already
offers an abstraction layer over several messaging brokers. Undergo some
kind of proof of concept to see if such a thing is possible and how.

# Kafka integration

Kafka is a powerful messaging broker technology that covers lots
of features and functionalities that could provide some ideas
to the current features that melange provides.
