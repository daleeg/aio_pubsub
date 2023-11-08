import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
from aiopubsub import Pubsub, PubsubRole


async def print_msg(channel, msg):
    print(f"pmsg: {channel} -- {msg}")


async def main():
    channels = ["foo*"]
    async with Pubsub(Pubsub.REDIS, port=16379, namespace="cs", role=PubsubRole.SUB) as psub:
        await psub.psubscribe(*channels)
        async for k in psub.listen(handler=print_msg):
            print(k)
        await psub.unsubscribe(*channels)


if __name__ == '__main__':
    asyncio.run(main())
