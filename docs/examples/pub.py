import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
from aiopubsub import Pubsub


async def main():
    pubpub = Pubsub(Pubsub.REDIS, port=16379)
    count = await pubpub.publish("foo", {"test": 1})
    print(count)
    async with pubpub.get_pub(namespace="cs") as pub:
        count = await pub.publish("foo", {"test": 2})
        print(count)
        count = await pub.publish("foo", {"test": 3})
        print(count)
    await pubpub.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
