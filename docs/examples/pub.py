import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
from aiopubsub import Pubsub


async def main():
    pub = Pubsub(Pubsub.REDIS, port=16379)
    count = await pub.publish("foo1", {"test": 1})
    print(count)
    async with pub.get_pub() as _pub:
        count = await pub.publish("foo1", {"test": 2}, _conn=_pub.conn)
        print(count)
        count = await pub.publish("foo1", {"test": 3}, _conn=_pub.conn)
        print(count)
    await pub.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
