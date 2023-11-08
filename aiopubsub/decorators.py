import asyncio
import functools


def init_pub(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        self.set_role(PubsubRole.PUB)
        await self.acquire()
        return await func(self, *args, **kwargs)

    return wrapper


def init_sub(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        self.set_role(PubsubRole.SUB)
        await self.acquire()
        return await func(self, *args, **kwargs)

    return wrapper


class PubsubRole(object):
    PUB = "pub"
    SUB = "sub"

    def __init__(self, role=None):
        self.role = role

    def clear(self):
        self.role = None

    def set(self, role):
        if self.role is None:
            self.role = role
        elif self.role != role:
            raise ValueError(f"role is already set {self.role}")

def process_timeout(func):
    not_set = "NOT_SET"

    @functools.wraps(func)
    async def _timeout(self, *args, timeout=not_set, **kwargs):
        timeout = self.timeout if timeout == not_set else timeout
        if timeout == 0 or timeout is None:
            return await func(self, *args, **kwargs)
        return await asyncio.wait_for(func(self, *args, **kwargs), timeout)

    return _timeout