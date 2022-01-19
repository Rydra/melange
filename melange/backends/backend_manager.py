from typing import Optional

from singleton import Singleton

from melange.backends.interfaces import MessagingBackend


class BackendManager(metaclass=Singleton):
    """
    This class should be used to initialize the type of messaging provider you
    want to use (Rabbit, AWS, etc)
    """

    def __init__(self) -> None:
        self._backend: Optional[MessagingBackend] = None

    def use_backend(
        self,
        backend: MessagingBackend,
    ) -> None:
        if not isinstance(backend, MessagingBackend):
            raise Exception("Invalid backend supplied")

        self._backend = backend

    def get_backend(self) -> MessagingBackend:
        if not self._backend:
            raise Exception(
                "No backend is registered. Please call 'use_backend' prior to getting it"
            )

        return self._backend
