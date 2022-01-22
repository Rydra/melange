# Setting the default messaging backend

To instantiate a publishers or a consumer, you need to pass
a `MessagingBackend` as a constructor argument. Depending on the circumstances,
however, this might feel repetitive.

As an alternative, you could use the singleton `BackendManager` and register
a backend for global usage in your initialization code:

``` py
BackendManager().set_default_backend(AWSBackend())
```

From that point forward, any instantiation of a Publisher or Consumer
does not need a backend as an argument anymore. Revisiting one of the
recurring examples of this documentation, we could use the `BackendManager`
like this.

``` py title="Usage of the backend manager"
--8<-- "melange/examples/doc_examples/backend_manager.py"
```

Notice that we are not passing the backend now as a parameter
when creating the `QueuePublisher` object, since it will retrieve
it from the BackendManager.

!!! warning

    Use the BackendManager with caution though.
    Singletons are [regarded sometimes as an antipattern](https://stackoverflow.com/questions/12755539/why-is-singleton-considered-an-anti-pattern)
    depending on the situation, and dependency injection is usually regarded
    as a cleaner solution to construct objects.
