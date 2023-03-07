import asyncio
import logging
import typing

from cacheout import LFUCache

from item_store.core import BaseCore, MemoryCache
from item_store.structure.proto_structure.all import *

logger = logging.getLogger(__name__)


class CacheBase(BaseCore):
    delete_delay = 0.1
    cache_key_format = 'item_store:{item_type}:{item_id}'
    cache_ttl = 86400 * 2
    cache_memory = MemoryCache(LFUCache(maxsize=10000, ttl=60))

    def get_cache_key(self, item: ItemDoc):
        return self.cache_key_format.format(item_type=item.item_type, item_id=item.item_id)

    async def update_cache_ttl(self, items: typing.List[ItemDoc]) -> bool:
        return await self.save_cache(items, only_update_ttl=True)

    async def save_cache(self, items: typing.List[ItemDoc], only_update_ttl=False) -> bool:
        ...

    async def delete_cache(self, items: typing.List[ItemDoc]) -> bool:
        ...

    async def get_cache(self, items: typing.List[ItemDoc]) -> typing.List[ItemDoc]:
        ...

    async def save(self, items: typing.List[ItemDoc]) -> bool:
        state = False
        try:
            state = await self.run_async_func(self.save_cache, items)
            logger.debug('cache_save state=%s items=%s', state, items)
            asyncio.create_task(self.run_async_func(self.cache_memory.set_many_items, items))
        except Exception as e:
            logger.error(f'cache_save_error {e=} {items=}')
        return state

    async def get(self, items: typing.List[ItemDoc]) -> typing.List[ItemDoc]:
        cache_items = []
        try:
            memory_items = self.cache_memory.get_many_items(items)
            cache_uniq_ids = self.get_items_uniq_ids(items=memory_items)
            if memory_items:
                cache_items.extend(memory_items)
            not_memory_items = [item for item in items if self.get_item_uniq_id(item) not in cache_uniq_ids]
            if not_memory_items:
                cache_not_memory_items = await self.run_async_func(self.get_cache, not_memory_items)
                cache_items += cache_not_memory_items
                asyncio.create_task(self.run_async_func(self.cache_memory.add_many_items, cache_items))
            logger.debug('cache_get cache_items=%s items=%s', cache_items, items)
            if cache_items:
                asyncio.create_task(self.run_async_func(self.update_cache_ttl, cache_items))
        except Exception as e:
            logger.error(f'cache_get_error {e=} {items=}')
        return cache_items

    async def delete(self, items: typing.List[ItemDoc]) -> bool:
        state = False
        try:
            asyncio.create_task(self.run_async_func(self.cache_memory.delete_many_items, items))
            await asyncio.sleep(self.delete_delay)
            state = await self.run_async_func(self.delete_cache, items)
            logger.debug('cache_delete state=%s items=%s', state, items)
        except Exception as e:
            logger.error(f'cache_delete_error {e=} {items=}')
        return state
