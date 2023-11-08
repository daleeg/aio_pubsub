from .base import BasePubsub
from ..backend.redis_ import RedisBackend


class RedisPubsub(BasePubsub):
    NAME = "redis"
    backend_class = RedisBackend

    def __repr__(self):
        return f"RedisPubsub ({self.host}:{self.port}/{self.db})"
