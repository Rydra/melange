from typing import Optional

from singleton import Singleton

from melange.backends.interfaces import MessagingBackend


class BackendManager(metaclass=Singleton):
    def __init__(self) -> None:
        self._backend: Optional[MessagingBackend] = None

    def set_default_backend(
        self,
        backend: MessagingBackend,
    ) -> None:
        """
        Sets the default backend
        Args:
            backend:
        """
        if not isinstance(backend, MessagingBackend):
            raise Exception("Invalid backend supplied")

        self._backend = backend

    def get_default_backend(self) -> MessagingBackend:
        """
        Returns the current default backend
        """
        if not self._backend:
            raise Exception(
                "No backend is registered. Please call 'set_default_backend' prior to getting it"
            )

        return self._backend
