import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, os.pardir ))
from aiopubsub import Pubsub


async def main():
    pubsub = Pubsub(Pubsub.REDIS, port=16379)

    async with pubsub.get_sub(namespace="cs") as psub:
        await psub.psubscribe("foo*")
        async for k in psub.listen():
            print(k)
    await pubsub.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
