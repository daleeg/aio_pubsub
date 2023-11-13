import logging
from typing import Dict, Type

from .pubsub import BasePubsub
from .constant import PubsubRole

__version__ = "1.0.9"


def int_or_str(value):
    try:
        return int(value)
    except ValueError:
        return value


VERSION = tuple(map(int_or_str, __version__.split(".")))
LOG = logging.getLogger(__name__)

PUBSUB_CACHES: Dict[str, Type[BasePubsub]] = {}

try:
    import redis
except ImportError:
    LOG.info("aioredis not installed, RedisCache unavailable")
else:
    from .pubsub.redis_ import RedisPubsub

    PUBSUB_CACHES[RedisPubsub.NAME] = RedisPubsub
    del redis


class Pubsub:
    REDIS = PUBSUB_CACHES[RedisPubsub.NAME]

    def __new__(cls, pubsub_class=REDIS, **kwargs):
        if not issubclass(pubsub_class, BasePubsub):
            raise TypeError("Invalid cache type, you can only use {}".format(list(PUBSUB_CACHES.keys()))
                            )
        instance = pubsub_class.__new__(pubsub_class, **kwargs)
        instance.__init__(**kwargs)
        return instance


__all__ = [
    "Pubsub",
    "PubsubRole"
]
