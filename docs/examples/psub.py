import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, os.pardir ))
from aiopubsub import Pubsub


async def main():
    sub = Pubsub(Pubsub.REDIS, port=16379)

    async with sub.get_sub() as _sub:
        _conn = await sub.psubscribe("foo*", _conn=_sub.conn)
        async for k in sub.listen(_conn=_conn):
            print(k)
    await sub.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
