import aioredis
import re

__all__ = ["RedisPubsub"]


def get_redis_version():
    version1_reg = re.compile(r"^1.*")
    version2_reg = re.compile(r"^[2-9].*")
    redis_version = aioredis.__version__
    if version1_reg.match(redis_version):
        return 1
    elif version2_reg.match(redis_version):
        return 2
    return 0


_version = get_redis_version()
if _version == 1:
    from .redis import RedisPubsub
elif _version == 2:
    from .redis2 import RedisPubsub
else:
    raise ImportError(f"unsupported version aioredis: {aioredis.__version__}")
