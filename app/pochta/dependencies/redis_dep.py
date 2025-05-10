from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis

from app.common.config import redis_pool


async def get_redis_connection() -> Redis[str]:
    # TODO nq add backoff?
    return Redis(connection_pool=redis_pool, decode_responses=True)


RedisConnection = Annotated[Redis[str], Depends(get_redis_connection)]
