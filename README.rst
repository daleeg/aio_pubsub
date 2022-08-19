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
        pub = Pubsub(Pubsub.REDIS, port=16379)
        count = await pub.publish("foo1", {"test": 1})
        print(count)
        async with pub.get_pub() as _pub:
            count = await pub.publish("foo1", {"test": 2}, _conn=_pub.conn)
            print(count)
            count = await pub.publish("foo1", {"test": 3}, _conn=_pub.conn)
            print(count)
        await pub.close()

- 2.2 订阅

.. code-block:: python

    from aiopubsub import Pubsub

    async def main():
        sub = Pubsub(Pubsub.REDIS, port=16379)

        async with sub.get_sub() as _sub:
            _conn = await sub.subscribe("foo", _conn=_sub.conn)
            async for k in sub.listen(_conn):
                print(k)
        await sub.close()

- 2.3 模糊订阅

.. code-block:: python

    from aiopubsub import Pubsub

    async def main():
        sub = Pubsub(Pubsub.REDIS, port=16379)

        async with sub.get_sub() as _sub:
            _conn = await sub.psubscribe("foo*", _conn=_sub.conn)
            async for k in sub.listen(_conn=_conn):
                print(k)
        await sub.close()


