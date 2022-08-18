import asyncio
import functools
import logging

from .serializer import JsonSerializer

LOG = logging.getLogger(__name__)


def process_timeout(func):
    not_set = "NOT_SET"

    @functools.wraps(func)
    async def _timeout(self, *args, timeout=not_set, **kwargs):
        timeout = self.timeout if timeout == not_set else timeout
        if timeout == 0 or timeout is None:
            return await func(self, *args, **kwargs)
        return await asyncio.wait_for(func(self, *args, **kwargs), timeout)

    return _timeout


class BasePubsub(object):
    NAME: str

    def __init__(self, serializer=None, namespace=None, key_builder=None, timeout=500):
        self.namespace = namespace
        self.timeout = timeout
        self.build_key = key_builder or self._build_key
        self._serializer = serializer or JsonSerializer()

    @property
    def serializer(self):
        return self._serializer

    def _build_key(self, key, namespace=None):
        if namespace is not None:
            return f"{namespace}:{key}"
        if self.namespace is not None:
            return f"{self.namespace}:{key}"
        return key

    @process_timeout
    async def unsubscribe(self, channel, *channels, namespace=None, _conn=None):
        ns_channels = [self.build_key(c, namespace=namespace) for c in (channel, *channels)]
        return await self._unsubscribe(*ns_channels, _conn=_conn)

    @process_timeout
    async def publish(self, channel, data, dumps_fn=None, namespace=None, _conn=None):
        dumps = dumps_fn or self._serializer.dumps
        ns_channel = self.build_key(channel, namespace=namespace)
        message = dumps(data)
        ret = await self._publish(ns_channel, message, _conn=_conn)
        if ret == 0:
            LOG.warning(f"No client subscribe channel[{ns_channel}], message is dropped: {message}")
        return ret

    @process_timeout
    async def subscribe(self, channel, *channels, _conn=None, namespace=None):
        ns_channels = [self.build_key(c, namespace=namespace) for c in (channel, *channels)]
        return await self._subscribe(*ns_channels, _conn=_conn)

    @process_timeout
    async def psubscribe(self, pattern, *patterns, _conn=None, namespace=None):
        ns_channels = [self.build_key(c, namespace=namespace) for c in (pattern, *patterns)]
        return await self._psubscribe(*ns_channels, _conn=_conn)

    @process_timeout
    async def punsubscribe(self, pattern, *patterns, namespace=None, _conn=None):
        ns_channels = [self.build_key(c, namespace=namespace) for c in (pattern, *patterns)]
        return await self._punsubscribe(*ns_channels, _conn=_conn)

    async def listen(self, loads_fn=None, _conn=None):
        loads = loads_fn or self._serializer.loads
        async for k in self._listen(_conn):
            k["data"] = loads(k["data"])
            yield k

    @process_timeout
    async def unsubscribe(self, channel, *channels, _conn=None, namespace=None):
        ns_channels = [self.build_key(c, namespace=namespace) for c in (channel, *channels)]
        return await self._unsubscribe(*ns_channels, _conn=_conn)

    @process_timeout
    async def close(self, *args, _conn=None, **kwargs):
        return await self._close(*args, _conn=_conn, **kwargs)

    def get_pub(self):
        return _Pub(self)

    def get_sub(self):
        return _Sub(self)

    async def acquire_sub(self):
        return await self._acquire_sub()

    async def release_sub(self, _conn):
        return await self._release_sub(_conn)

    async def acquire_pub(self):
        return await self._acquire_pub()

    async def release_pub(self, _conn):
        return await self._release_pub(_conn)


class _Pub(object):
    def __init__(self, _pubsub):
        self._pubsub = _pubsub
        self.conn = None

    async def __aenter__(self):
        self.conn = await self._pubsub.acquire_pub()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self._pubsub.release_pub(self.conn)

    def __getattr__(self, name):
        return self._pubsub.__getattribute__(name)


class _Sub(object):
    def __init__(self, _pubsub):
        self._pubsub = _pubsub
        self.conn = None

    async def __aenter__(self):
        self.conn = await self._pubsub.acquire_sub()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self._pubsub.release_sub(self.conn)

    def __getattr__(self, name):
        return self._pubsub.__getattribute__(name)
