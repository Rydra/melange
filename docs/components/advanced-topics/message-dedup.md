# Message de-duplication

Distributed architectures are hard, complex and come with a good deal of burdens, but they are required to achieve levels of scalability
and isolation harder to achieve on monolithic architectures. One of this issues is the possibility of
of the same message being received twice by the listeners. Network failures, application crashes, etc...
can cause this issue which, if not though or left undealt can cause your system to be out of sync and
run in an inconsistent state. This is why you need to take measures.

One of this measures is to, simply, write your listeners to be *idempotent*. This means that it does not
matter how many times a listener is called, the result will be the same and it won't impact or leave
the system into an inconsistent state.

However, sometimes writing idempotent code is just not possible. You require **message deduplication** to
account for this and ensure that a message won't be sent twice. You could use Amazon SQS FIFO Queues which
they say they provide this message deduplication, though not only FIFO queues are more expensive than
standard ones, [but exactly-once delivery is just impossible](https://dzone.com/articles/fifo-exactly-once-and-other-costs).
In Melange we have accounted for this with a *cache interface* that you can supply
to the `ConsumerHandler` (like a *Redis cache*) that will control that no message is delivered twice to the same consumer.

In Melange we provide a `RedisCache` class that you could use to perform this message deduplication. However
we do not want to tie the library to any specific technology, so as long as you comply
with the `DeduplicationCache` interface it will work just fine.

> The cache for message deduplication is completely optional, but on a production environment having some
kind of cache to handle deduplication is encouraged.

This is the `DeduplicationCache` specification:

::: melange.infrastructure.cache.DeduplicationCache
