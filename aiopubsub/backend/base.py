import abc


class BaseBackend(metaclass=abc.ABCMeta):

    async def acquire(self):
        ...

    async def release(self):
        ...

    async def unsubscribe(self, channel, *channels):
        ...

    async def subscribe(self, channel, *channels):
        ...

    async def psubscribe(self, pattern, *patterns):
        ...

    async def punsubscribe(self, pattern, *patterns):
        ...

    async def listen(self, timeout=None):
        ...

    async def publish(self, channel, message):
        ...

    async def _close(self, *args, **kwargs):
        ...
