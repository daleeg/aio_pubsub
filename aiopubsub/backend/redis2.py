import asyncio
import functools
import logging

import aioredis

from aiopubsub.base import BasePubsub

LOG = logging.getLogger(__name__)


def init_pub(func):
    @functools.wraps(func)
    async def wrapper(self, *args, _conn=None, **kwargs):
        if _conn is None:
            redis = await self._get_redis()
            async with redis.client() as _conn:
                return await func(self, *args, _conn=_conn, **kwargs)
        return await func(self, *args, _conn=_conn, **kwargs)

    return wrapper


def init_sub(func):
    @functools.wraps(func)
    async def wrapper(self, *args, _conn=None, **kwargs):
        if _conn is None:
            redis = await self._get_redis()
            async with redis.pubsub() as _conn:
                return await func(self, *args, _conn=_conn, **kwargs)
        return await func(self, *args, _conn=_conn, **kwargs)

    return wrapper


class RedisBackend:
    def __init__(self, host="127.0.0.1", port=6379, db=0, password=None,
                 loop=None, socket_connect_timeout=None,
                 **kwargs):
        super().__init__(**kwargs)
        self.host = host
        self.port = int(port)
        self.db = db
        self._loop = loop
        socket_connect_timeout = (float(socket_connect_timeout) if socket_connect_timeout else None)
        self.kwargs = {"db": int(db), "password": password, "decode_responses": True,
                       "socket_connect_timeout": socket_connect_timeout}

        self.__redis_lock = None

        self._redis: aioredis.Redis = None

    @property
    def _redis_lock(self):
        if self.__redis_lock is None:
            self.__redis_lock = asyncio.Lock()
        return self.__redis_lock

    async def _acquire_sub(self, _receiver: aioredis.client.PubSub = None):
        await self._get_redis()
        if not _receiver:
            _receiver = self._redis.pubsub()
        return _receiver, _receiver

    async def _release_sub(self, _conn: aioredis.client.PubSub, receiver):
        return await _conn.reset()

    async def _acquire_pub(self):
        await self._get_redis()
        return await self._redis.client().initialize()

    async def _release_pub(self, _conn: aioredis.Redis):
        return await _conn.close()

    @init_sub
    async def _unsubscribe(self, channel, *channels, _conn: aioredis.client.PubSub = None, receiver=None):
        return await _conn.unsubscribe(channel, *channels)

    @init_sub
    async def _subscribe(self, channel, *channels, _conn: aioredis.client.PubSub = None, receiver=None):
        sub_channels = channel, *channels
        ret = await _conn.subscribe(*sub_channels)
        LOG.info(f"sub: {sub_channels}, ret: {ret}")

    @init_sub
    async def _psubscribe(self, pattern, *patterns, _conn: aioredis.client.PubSub = None, receiver=None):
        psub_patterns = pattern, *patterns
        ret = await _conn.psubscribe(*psub_patterns)
        LOG.info(f"psub: {psub_patterns}, ret: {ret}")

    @init_sub
    async def _punsubscribe(self, pattern, *patterns, _conn: aioredis.client.PubSub = None, receiver=None):
        return await _conn.punsubscribe(pattern, *patterns)

    async def _listen(self, _conn: aioredis.client.PubSub = None, receiver=None):
        """Listen for messages on channels this client has been subscribed to"""
        async for k in _conn.listen():
            if not k["type"] in ["pmessage", "message"]:
                continue
            yield k

    @init_pub
    async def _publish(self, channel, message, _conn: aioredis.client.Redis = None):
        return await _conn.publish(channel, message)

    async def _close(self, *args, **kwargs):
        if self._redis is not None:
            await self._redis.close()

    async def _get_redis(self):
        async with self._redis_lock:
            if self._redis is None:
                url = f"redis://{self.host}:{self.port}"
                self._redis = aioredis.from_url(url, **self.kwargs)
            return self._redis


class RedisPubsub(RedisBackend, BasePubsub):
    NAME = "redis"

    def __repr__(self):
        return f"RedisPubsub ({self.host}:{self.port}/{self.db})"
