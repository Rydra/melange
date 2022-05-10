from hamcrest import *

from melange.infrastructure.cache import RedisCache


class TestAsyncCache:
    def test_store_to_redis_cache(self):
        cache = RedisCache(host="redis", port=6379, db=0, password=None, expire=3600)

        cache.store("potato", "falafel")
        value = cache.get("potato")
        assert_that(value, is_("falafel"))
        assert_that(cache.contains("potato"), is_(True))
        assert_that(cache.contains("banana"), is_(False))
