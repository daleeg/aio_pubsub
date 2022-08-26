aio_pubsub
########


1. 安装
==========

.. code-block:: shell

   pip install aiopubsub-py3
   pip install aiopubsub-py3[redis]
   pip install aiopubsub-py3[redis2]

2. 示例
==========

- 2.1 发布

.. code-block:: python

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

- 2.2 订阅

.. code-block:: python

    from aiopubsub import Pubsub

    async def main():
        pubsub = Pubsub(Pubsub.REDIS, port=16379)

        async with pubsub.get_sub(namespace="cs") as sub:
            await sub.subscribe("foo")
            async for k in sub.listen():
                print(k)
        await pubsub.close()

- 2.3 模糊订阅

.. code-block:: python

    from aiopubsub import Pubsub

    async def main():
        pubsub = Pubsub(Pubsub.REDIS, port=16379)
        async with pubsub.get_sub(namespace="cs") as psub:
            await psub.psubscribe("foo*")
            async for k in psub.listen():
                print(k)
        await pubsub.close()


