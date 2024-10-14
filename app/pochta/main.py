from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from app.common.fastapi_ext import APIRouterExt
from app.common.redis_ext import RedisRouter
from app.pochta.routes import pochta_mub
from app.pochta.workers import pochta_rds
from app.users.utils.mub import MUBProtection

mub_router = APIRouterExt(prefix="/mub", dependencies=[MUBProtection])
mub_router.include_router(pochta_mub.router, prefix="/pochta-service")

api_router = APIRouterExt()
api_router.include_router(mub_router)

redis_router = RedisRouter()
redis_router.include_router(pochta_rds.router)


@asynccontextmanager
async def lifespan() -> AsyncIterator[None]:
    await redis_router.run_consumers()
    yield
    await redis_router.terminate_consumers()
