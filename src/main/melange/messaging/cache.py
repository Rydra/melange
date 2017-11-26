from redis_cache import SimpleCache, logging

from melange import settings
from melange.infrastructure.singleton import Singleton


@Singleton
class Cache:
    def __init__(self):
        self.cache = SimpleCache(expire=3600,
                                 host=settings.CACHE_REDIS_HOST,
                                 port=settings.CACHE_REDIS_PORT,
                                 db=settings.CACHE_REDIS_DB,
                                 password=settings.CACHE_REDIS_PASSWORD,
                                 namespace=settings.CACHE_NAMESPACE)

        if not self.cache.connection:
            logging.warning("Could not establish a connection with redis. Message deduplication won't work")

    def store(self, key, value, expire=None):
        if not self.cache.connection:
            return

        return self.cache.store(key, value, expire)

    def get(self, key):
        if not self.cache.connection:
            return

        return self.cache.get(key)

    def __contains__(self, key):
        return self.cache.connection and key in self.cache
