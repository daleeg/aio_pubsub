import asyncio
import logging

import redis.asyncio as aioredis

from .base import BaseBackend
from .. import PubsubRole
from ..decorators import init_sub, init_pub

LOG = logging.getLogger(__name__)


class RedisBackend(BaseBackend):
    def __init__(self, host="127.0.0.1", port=6379, db=0, password=None,
                 socket_connect_timeout=None,
                 role=None,
                 redis_: aioredis.client.Redis = None,
                 pubsub_: aioredis.client.PubSub = None,
                 **kwargs):

        self._redis_lock = asyncio.Lock()
        self.role = PubsubRole(role)
        self._client: aioredis.client.Redis | aioredis.client.PubSub = None

        if role == PubsubRole.SUB:
            self._client = redis_
            self.get_client = self._get_pubsub
        elif role == PubsubRole.PUB:
            self.get_client = self._get_redis
            self._client = pubsub_
        if self._client:
            kwargs = self._client.connection_pool.connection_kwargs
            self.host = kwargs["host"]
            self.port = kwargs["port"]
            self.kwargs = {"db": kwargs["db"], "password": kwargs["socket_connect_timeout"], "decode_responses": True,
                           "socket_connect_timeout": kwargs["socket_connect_timeout"]}
        else:
            self.host = host
            self.port = int(port)
            socket_connect_timeout = (float(socket_connect_timeout) if socket_connect_timeout else None)
            self.kwargs = {"db": int(db), "password": password, "decode_responses": True,
                           "socket_connect_timeout": socket_connect_timeout}

    def set_role(self, role):
        self.role.set(role)
        if role == PubsubRole.SUB:
            self.get_client = self._get_pubsub
        else:
            self.get_client = self._get_redis

    async def acquire(self):
        if self._client is None:
            async with self._redis_lock:
                self._client = self.get_client()
        return self._client

    async def release(self):
        await self.close()

    @init_sub
    async def unsubscribe(self, channel, *channels):
        return await self._client.unsubscribe(channel, *channels)

    @init_sub
    async def subscribe(self, channel, *channels):
        sub_channels = channel, *channels
        ret = await self._client.subscribe(*sub_channels)
        LOG.info(f"sub: {sub_channels}, ret: {ret}")

    @init_sub
    async def psubscribe(self, pattern, *patterns):
        psub_patterns = pattern, *patterns
        ret = await self._client.psubscribe(*psub_patterns)
        LOG.info(f"psub: {psub_patterns}, ret: {ret}")

    @init_sub
    async def punsubscribe(self, pattern, *patterns):
        return await self._client.punsubscribe(pattern, *patterns)

    async def listen(self, timeout=None):
        self.set_role(PubsubRole.SUB)
        await self.acquire()
        LOG.info(f"start listen: {self._client.channels}")

        while True:
            await asyncio.sleep(0)

            if self._client.subscribed:
                try:
                    response = await self._client.get_message(ignore_subscribe_messages=True, timeout=timeout)
                except asyncio.CancelledError:
                    break
                except BaseException as e:
                    LOG.error(e)
                    continue

                if response:
                    LOG.debug(response)
                    if not response["type"] in ["pmessage", "message"]:
                        continue
                    yield response
        LOG.info(f"stop listen: {self._client.channels}")

    @init_pub
    async def publish(self, channel, message):
        return await self._client.publish(channel, message)

    async def close(self):
        if self._client:
            async with self._redis_lock:
                await self._client.aclose()
                self._client = None
                self.role.clear()
                self.get_client = None

    def _get_redis(self):
        url = f"redis://{self.host}:{self.port}"
        return aioredis.from_url(url, **self.kwargs)

    def _get_pubsub(self):
        return self._get_redis().pubsub()
