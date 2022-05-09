from hamcrest import *

from melange.infrastructure.async_cache import AsyncRedisCache


class TestAsyncCache:
    async def test_store_to_redis_cache(self, anyio_backend):
        cache = AsyncRedisCache(
            host="redis", port=6379, db=0, password=None, expire=3600
        )

        await cache.store("potato", "falafel")
        value = await cache.get("potato")
        assert_that(value, is_("falafel"))
        assert_that(await cache.contains("potato"), is_(True))
        assert_that(await cache.contains("banana"), is_(False))
