from typing import Any, Dict, Optional

from singleton import Singleton

from melange.backends.interfaces import MessagingBackend


class BackendManager(metaclass=Singleton):
    """
    This class should be used to initialize the type of messaging provider you
    want to use (Rabbit, AWS, etc)
    """

    def __init__(self) -> None:
        self._backend: Optional[MessagingBackend] = None
        self._backends: Dict[str, Any] = {}

    def add_available_backends(self, **kwargs: Any) -> None:
        self._backends.update(kwargs)

    def use_backend(
        self,
        backend: Optional[MessagingBackend] = None,
        backend_name: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        if backend:
            if not isinstance(backend, MessagingBackend):
                raise Exception("Invalid backend supplied")

            self._backend = backend

        elif backend_name:
            backend = self._backends.get(backend_name)
            if not backend:
                raise Exception("Invalid backend supplied")

            self._backend = backend(**kwargs)

        else:
            raise Exception("You need to either supply a backend or a backend_name!")

    def get_backend(self) -> MessagingBackend:
        if not self._backend:
            raise Exception(
                "No backend is registered. Please call 'use_backend' prior to getting it"
            )

        return self._backend
