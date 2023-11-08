import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
from aiopubsub import Pubsub, PubsubRole


async def main():
    async with Pubsub(Pubsub.REDIS, port=16379, namespace="cs", role=PubsubRole.PUB) as pub:
        count = await pub.publish("foo", {"test": 1})
        print(count)
        count = await pub.publish("foo", {"test": 2})
        print(count)
        count = await pub.publish("foo", {"test": 3})
        print(count)


if __name__ == '__main__':
    asyncio.run(main())
