import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
from aiopubsub import Pubsub, PubsubRole


async def print_msg(channel, msg):
    print(f"sub msg: {channel} -- {msg}")


async def main():
    channels = ["foo"]
    async with Pubsub(Pubsub.REDIS, port=16379, namespace="cs", role=PubsubRole.SUB) as sub:
        await sub.subscribe(*channels)
        async for k in sub.listen(handler=print_msg):
            print(k)
        await sub.unsubscribe(*channels)


if __name__ == '__main__':
    asyncio.run(main())
