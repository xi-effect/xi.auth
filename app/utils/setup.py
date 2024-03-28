from asyncio import AbstractEventLoop, get_running_loop

from aio_pika import connect_robust
from aio_pika.abc import AbstractRobustConnection

from app.common.config import MQ_URL, Base, engine, pochta_producer


async def reinit_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def connect_rabbit() -> AbstractRobustConnection:
    loop: AbstractEventLoop = get_running_loop()
    connection = await connect_robust(MQ_URL, loop=loop)
    await pochta_producer.connect(connection)
    return connection
