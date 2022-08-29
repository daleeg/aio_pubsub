import asyncio
import functools
import logging
from functools import partial

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
        return f":{key}"

    def _parser_key(self, key: str, namespace=None):
        _n, _k = key.split(":", 1)
        if _n not in ["", namespace, self.namespace]:
            if namespace and _n != namespace:
                LOG.warning(f"bad channel: {key} ns:{namespace}")
            elif self.namespace and _n != self.namespace:
                LOG.warning(f"bad channel: {key} ns:{self.namespace}")
            elif _n != "":
                LOG.warning(f"bad channel: {key}")
        return _k

    def _parser_pattern(self, pattern: str):
        return pattern.split(":", 1)[1]

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
    async def subscribe(self, channel, *channels, namespace=None, _conn=None):
        ns_channels = [self.build_key(c, namespace=namespace) for c in (channel, *channels)]
        await self._subscribe(*ns_channels, _conn=_conn)

    @process_timeout
    async def unsubscribe(self, channel, *channels, namespace=None, _conn=None):
        ns_channels = [self.build_key(c, namespace=namespace) for c in (channel, *channels)]
        return await self._unsubscribe(*ns_channels, _conn=_conn)

    @process_timeout
    async def psubscribe(self, pattern, *patterns, namespace=None, _conn=None):
        ns_channels = [self.build_key(c, namespace=namespace) for c in (pattern, *patterns)]
        await self._psubscribe(*ns_channels, _conn=_conn)

    @process_timeout
    async def punsubscribe(self, pattern, *patterns, namespace=None, _conn=None):
        ns_channels = [self.build_key(c, namespace=namespace) for c in (pattern, *patterns)]
        return await self._punsubscribe(*ns_channels, _conn=_conn)

    async def listen(self, loads_fn=None, namespace=None, _conn=None):
        loads = loads_fn or self._serializer.loads
        async for k in self._listen(_conn):
            k["data"] = loads(k["data"])
            k["channel"] = self._parser_key(k["channel"], namespace)
            if k["type"] == "pmessage":
                k["pattern"] = self._parser_pattern(k["pattern"])
            yield k

    @process_timeout
    async def unsubscribe(self, channel, *channels, namespace=None, _conn=None):
        ns_channels = [self.build_key(c, namespace=namespace) for c in (channel, *channels)]
        return await self._unsubscribe(*ns_channels, _conn=_conn)

    @process_timeout
    async def close(self, *args, **kwargs):
        return await self._close(*args, **kwargs)

    def get_pub(self, namespace=None):
        return _Pub(self, namespace)

    def get_sub(self, namespace=None):
        return _Sub(self, namespace)

    async def acquire_sub(self):
        return await self._acquire_sub()

    async def release_sub(self, _conn):
        return await self._release_sub(_conn)

    async def acquire_pub(self):
        return await self._acquire_pub()

    async def release_pub(self, _conn):
        return await self._release_pub(_conn)


class BasePubsubEntity(object):
    __slots__ = ["_pubsub", "_namespace", "_conn"]

    def __init__(self, _pubsub, namespace):
        self._pubsub = _pubsub
        self._namespace = namespace
        self._conn = None

    def __getattr__(self, name):
        if name in self.__slots__:
            return partial(self._pubsub.__getattribute__(name), namespace=self._namespace, _conn=self._conn)
        else:
            return self._pubsub.__getattribute__(name)


class _Pub(BasePubsubEntity):
    __slots__ = [
        "_pubsub", "_namespace", "_conn", "publish"
    ]

    async def __aenter__(self):
        self._conn = await self._pubsub.acquire_pub()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self._pubsub.release_pub(self._conn)


class _Sub(BasePubsubEntity):
    __slots__ = [
        "_pubsub", "_namespace", "_conn", "subscribe", "unsubscribe", "psubscribe", "punsubscribe", "listen"
    ]

    async def __aenter__(self):
        self._conn = await self._pubsub.acquire_sub()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self._pubsub.release_sub(self._conn)
