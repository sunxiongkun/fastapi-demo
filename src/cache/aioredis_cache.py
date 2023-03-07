import logging

import aioredis
from aioredis.client import Pipeline

from src.config.config import pic_web_redis
from cache import CacheBase

logger = logging.getLogger(__name__)


class RedisCache(CacheBase):
    cache = aioredis.Redis(**pic_web_redis)

    async def save_cache(self, items, only_update_ttl=False):
        cache_items = {
            self.get_cache_key(item=item): self.dump_item(item=item)
            for item in items
        }
        async with self.cache.pipeline() as pipe:  # type: Pipeline
            if not only_update_ttl:
                await pipe.mset(cache_items)
            for key in cache_items.keys():
                await pipe.expire(key, self.cache_ttl)
            pipe_res = await pipe.execute()

        state = all(pipe_res)
        return state

    async def delete_cache(self, items):
        delete_keys = [
            self.get_cache_key(item=item)
            for item in items
        ]
        await self.cache.delete(*delete_keys)
        return True

    async def get_cache(self, items):
        cache_keys = [
            self.get_cache_key(item=item)
            for item in items
        ]
        load_cache = await self.cache.mget(keys=cache_keys)
        load_items = [
            self.load_item(_load_cache)
            for _load_cache in load_cache if _load_cache is not None
        ]
        return load_items
