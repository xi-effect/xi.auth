from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis

from app.common.config import redis_pool


async def get_redis_connection() -> Redis:
    return Redis(connection_pool=redis_pool)


RedisConnection = Annotated[Redis, Depends(get_redis_connection)]
