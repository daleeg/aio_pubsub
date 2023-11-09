import asyncio
import functools
import inspect
import logging

from ..backend.base import BaseBackend
from ..decorators import process_timeout
from ..serializer import JsonSerializer
from ..types import SubHandler

LOG = logging.getLogger(__name__)


class BasePubsub(object):
    __slots__ = ["backend", "namespace", "timeout", "build_key", "_serializer"]
    backend_class = BaseBackend

    NAME: str

    def __init__(self, serializer=None, namespace=None, key_builder=None, timeout=500, **kwargs):
        self.namespace = namespace
        self.timeout = timeout
        self.build_key = key_builder or self._build_key
        self._serializer = serializer or JsonSerializer()
        self.backend = self.backend_class(**kwargs)

    @property
    def serializer(self):
        return self._serializer

    def _build_key(self, key, namespace=None):
        if namespace is not None:
            return f"{namespace}:{key}"
        if self.namespace is not None:
            return f"{self.namespace}:{key}"
        return f"{key}"

    def _parser_key(self, key: str, namespace=None):
        if not namespace:
            return key

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
    async def publish(self, channel, data, dumps_fn=None, namespace=None):
        dumps = dumps_fn or self._serializer.dumps
        ns_channel = self.build_key(channel, namespace=namespace)
        message = dumps(data)
        ret = await self.backend.publish(ns_channel, message)
        if ret == 0:
            LOG.warning(f"No client subscribe channel[{ns_channel}], message is dropped: {message}")
        return ret

    @process_timeout
    async def subscribe(self, channel, *channels, namespace=None):
        ns_channels = [self.build_key(c, namespace=namespace) for c in (channel, *channels)]
        await self.backend.subscribe(*ns_channels)

    @process_timeout
    async def unsubscribe(self, channel, *channels, namespace=None):
        ns_channels = [self.build_key(c, namespace=namespace) for c in (channel, *channels)]
        return await self.backend.unsubscribe(*ns_channels)

    @process_timeout
    async def psubscribe(self, pattern, *patterns, namespace=None):
        ns_channels = [self.build_key(c, namespace=namespace) for c in (pattern, *patterns)]
        await self.backend.psubscribe(*ns_channels)

    @process_timeout
    async def punsubscribe(self, pattern, *patterns, namespace=None):
        ns_channels = [self.build_key(c, namespace=namespace) for c in (pattern, *patterns)]
        return await self.backend.punsubscribe(*ns_channels)

    async def listen(self, loads_fn=None, namespace=None, timeout=None, handler: SubHandler = None):
        loads = loads_fn or self._serializer.loads
        async for k in self.backend.listen(timeout=timeout):
            k["data"] = loads(k["data"])
            k["channel"] = self._parser_key(k["channel"], namespace)
            if k["type"] == "pmessage":
                k["pattern"] = self._parser_pattern(k["pattern"])
            if handler:
                res = handler(k["channel"], k["data"])
                if inspect.isawaitable(res):
                    await res
            yield k

    @process_timeout
    async def unsubscribe(self, channel, *channels, namespace=None):
        ns_channels = [self.build_key(c, namespace=namespace) for c in (channel, *channels)]
        return await self.backend.unsubscribe(*ns_channels)

    @process_timeout
    async def close(self, *args, **kwargs):
        return await self.backend.close(*args, **kwargs)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()
