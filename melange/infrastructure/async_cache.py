import logging
from typing import Any, Optional, Protocol

import redis.exceptions
from redis import asyncio as aioredis  # type: ignore

logger = logging.getLogger(__name__)


class AsyncDeduplicationCache(Protocol):
    async def store(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        """
        Stores a key into the cache
        Args:
            key:
            value:
            expire: expiration time in seconds
        """
        raise NotImplementedError

    async def get(self, key: str) -> Any:
        """
        Retrieves the value stored under a key
        Args:
            key: the key to fetch in the cache

        Returns:
            The value stored under that key, or None
        """
        raise NotImplementedError

    async def contains(self, key: str) -> bool:
        raise NotImplementedError


class AsyncNullCache:
    """
    A cache that does nothing. Follows the Null Object Pattern.
    """

    async def store(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        pass

    async def get(self, key: str) -> Any:
        return None

    async def contains(self, key: str) -> bool:
        return False


class AsyncRedisCache:
    def __init__(self, **kwargs: Any) -> None:
        self.client = aioredis.Redis(
            host=kwargs.get("host"),
            port=kwargs.get("port"),
            db=kwargs.get("db"),
            password=kwargs.get("password"),
            decode_responses=True,
        )

    async def store(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        return await self.client.set(key, value, expire)

    async def get(self, key: str) -> Any:
        return await self.client.get(key)

    async def contains(self, key: str) -> bool:
        return bool(await self.client.exists(key))


async def get_async_redis_cache(
    null_if_no_connection: bool = False, **kwargs: Any
) -> AsyncDeduplicationCache:
    try:
        cache = AsyncRedisCache(**kwargs)
        if null_if_no_connection:
            await cache.client.ping()
        return cache
    except redis.exceptions.ConnectionError:
        return AsyncNullCache()
