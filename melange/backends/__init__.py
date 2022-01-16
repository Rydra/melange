from typing import Any

from melange.backends.backend_manager import BackendManager


def configure_exchange(backend_name: str, **kwargs: Any) -> None:
    BackendManager().use_backend(
        backend_name=backend_name,
        wait_time_seconds=kwargs.get("wait_time_seconds", 10),
        visibility_timeout=kwargs.get("visibility_timeout", 10),
    )
