from typing import Any


def get_fully_qualified_name(obj: Any) -> str:
    return obj.__module__ + "." + obj.__class__.__name__
