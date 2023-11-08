aio_pubsub
########


1. 安装
==========

.. code-block:: shell

   pip install aiopubsub-py3
   pip install aiopubsub-py3[redis]

2. 示例
==========

- 2.1 发布

.. code-block:: python

    from aiopubsub import Pubsub

    async def main():
        async with Pubsub(Pubsub.REDIS, port=16379, namespace="cs", role=PubsubRole.PUB) as pub:
            count = await pub.publish("foo", {"test": 1})
            print(count)
            count = await pub.publish("foo", {"test": 2})
            print(count)
            count = await pub.publish("foo", {"test": 3})
            print(count)

- 2.2 订阅

.. code-block:: python

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

- 2.3 模糊订阅

.. code-block:: python

    from aiopubsub import Pubsub

    async def print_msg(channel, msg):
        print(f"psub msg: {channel} -- {msg}")

    async def main():
        channels = ["foo*"]
        async with Pubsub(Pubsub.REDIS, port=16379, namespace="cs", role=PubsubRole.SUB) as psub:
            await psub.psubscribe(*channels)
            async for k in psub.listen(handler=print_msg):
                print(k)
            await psub.unsubscribe(*channels)


- 2.4 自动识别角色【根据第一次调用函数决策，未close之前不能切换角色】

.. code-block:: python

    from aiopubsub import Pubsub

    async def print_msg(channel, msg):
        print(f"psub msg: {channel} -- {msg}")

    async def main():
        channels = ["foo*"]
        pubsub = Pubsub(Pubsub.REDIS, port=16379, namespace="cs")
        await pubsub.publish("foo", {"test": 1})  # 角色设置为PUB，执行成功

        await pubsub.subscribe(*channels)  # 角色为PUB，无法订阅抛出异常

        await pubsub.close()  # 角色释放

        await pubsub.subscribe(*channels)  # 角色设置为SUB，执行成功

        print(pubsub.backend.role)

        await pubsub.publish("foo", {"test": 1})  # 角色为SUB，无法发布抛出异常

        async with pubsub:
            await pubsub.unsubscribe(*channels)  # 角色为SUB，执行成功
        # async with 退出作用域，角色释放

        await pubsub.publish("foo", {"test": 1})  # 角色设置为PUB，执行成功


