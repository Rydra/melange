import logging
from typing import Any, Optional, Protocol

import redis

logger = logging.getLogger(__name__)


class DeduplicationCache(Protocol):
    def store(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        """
        Stores a key into the cache
        Args:
            key:
            value:
            expire: expiration time in seconds
        """
        raise NotImplementedError

    def get(self, key: str) -> Any:
        """
        Retrieves the value stored under a key
        Args:
            key: the key to fetch in the cache

        Returns:
            The value stored under that key, or None
        """
        raise NotImplementedError

    def __contains__(self, key: str) -> bool:
        """
        Checks whether a certain key is present in the store

        Args:
            key: the key to check

        Returns:
            `True` if the value is present, `False` otherwise.
        """
        raise NotImplementedError


class NullCache:
    """
    A cache that does nothing. Follows the Null Object Pattern.
    """

    def store(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        pass

    def get(self, key: str) -> Any:
        return None

    def __contains__(self, key: str) -> bool:
        return False


class RedisCache:
    def __init__(self, **kwargs: Any) -> None:
        self.client = redis.Redis(
            host=kwargs.get("host", 3600),
            port=kwargs.get("port", 3600),
            db=kwargs.get("db", 3600),
            password=kwargs.get("password", 3600),
            decode_responses=True,
        )
        self.expire = kwargs.get("expire", 3600)

    def store(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        self.client.set(key, value, expire)

    def get(self, key: str) -> Any:
        return self.client.get(key)

    def contains(self, key: str) -> bool:
        return bool(self.client.exists(key))

    def __contains__(self, key: str) -> bool:
        return self.contains(key)


def get_redis_cache(
    null_if_no_connection: bool = False, **kwargs: Any
) -> DeduplicationCache:
    try:
        cache = RedisCache(**kwargs)
        if null_if_no_connection:
            cache.client.ping()
        return cache
    except redis.exceptions.ConnectionError:
        return NullCache()
