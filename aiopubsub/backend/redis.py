import asyncio
import functools

import aioredis
from aioredis.pubsub import Receiver

from aiopubsub.base import BasePubsub


def init_conn(func):
    @functools.wraps(func)
    async def wrapper(self, *args, _conn=None, **kwargs):
        if _conn is None:
            pool = await self._get_pool()
            conn_context = await pool
            with conn_context as _conn:
                _conn = aioredis.Redis(_conn)
                return await func(self, *args, _conn=_conn, **kwargs)
        return await func(self, *args, _conn=_conn, **kwargs)

    return wrapper


class RedisBackend:
    def __init__(self, host="127.0.0.1", port=6379, db=0, password=None,
                 loop=None, socket_connect_timeout=None,
                 pool_min_size=5, pool_max_size=20,
                 **kwargs):
        super().__init__(**kwargs)
        self.host = host
        self.port = int(port)
        self._loop = loop
        create_connection_timeout = (float(socket_connect_timeout) if socket_connect_timeout else None)
        self.kwargs = {"db": int(db), "password": password,
                       "create_connection_timeout": create_connection_timeout,
                       "encoding": "utf-8",
                       "minsize": pool_min_size,
                       "maxsize": pool_max_size,
                       }

        self.__pool_lock = None
        self._pool: aioredis.ConnectionsPool = None

    @property
    def _pool_lock(self):
        if self.__pool_lock is None:
            self.__pool_lock = asyncio.Lock()
        return self.__pool_lock

    async def _acquire_sub(self):
        await self._get_pool()
        conn = await self._pool.acquire()
        conn = aioredis.Redis(conn)
        return conn

    async def _release_sub(self, _conn: aioredis.Redis):
        self._pool.release(_conn.connection)
        return

    async def _acquire_pub(self):
        await self._get_pool()
        conn = await self._pool.acquire()
        conn = aioredis.Redis(conn)
        return conn

    async def _release_pub(self, _conn: aioredis.Redis):
        self._pool.release(_conn.connection)
        return

    @init_conn
    async def _unsubscribe(self, channel, *channels, _conn: aioredis.Redis = None):
        return await _conn.unsubscribe(channel, *channels)

    @init_conn
    async def _subscribe(self, channel, *channels, _conn: aioredis.Redis = None):
        mpsc = Receiver()
        ns_channels = [mpsc.channel(c) for c in (channel, *channels)]
        await _conn.subscribe(*ns_channels)
        return mpsc

    @init_conn
    async def _psubscribe(self, pattern, *patterns, _conn: aioredis.Redis = None):
        mpsc = Receiver()
        ns_patterns = [mpsc.pattern(p) for p in (pattern, *patterns)]
        await _conn.psubscribe(*ns_patterns)
        return mpsc

    @init_conn
    async def _punsubscribe(self, pattern, *patterns, _conn: aioredis.Redis = None):
        return await _conn.punsubscribe(pattern, *patterns)

    async def _listen(self, _conn: Receiver = None):
        """Listen for messages on channels this client has been subscribed to"""
        async for channel, msg in _conn.iter():
            if channel.is_pattern:
                channel_name, data = msg
                channel_name = channel_name.decode()
                data = data.decode()
                pattern = channel.name.decode()
                type_ = "pmessage"
            else:
                pattern = None
                type_ = "message"
                data = msg.decode()
                channel_name = channel.name.decode()
            yield {"type": type_, "pattern": pattern, "channel": channel_name, "data": data}

    @init_conn
    async def _publish(self, channel, message, _conn: aioredis.Redis = None):
        return await _conn.publish(channel, message)

    async def _close(self, *args, **kwargs):
        if self._pool is not None:
            await self._pool.clear()

    async def _get_pool(self):
        async with self._pool_lock:
            if self._pool is None:
                self._pool = await aioredis.create_pool((self.host, self.port), **self.kwargs)
            return self._pool


class RedisPubsub(RedisBackend, BasePubsub):
    NAME = "redis"

    def __repr__(self):
        return f"RedisPubsub ({self.host}:{self.port}/{self.db})"
