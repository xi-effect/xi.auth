import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from app.common.config import EMAIL_INITIALIZED, PRODUCTION_MODE
from app.common.fastapi_ext import APIRouterExt
from app.pochta.routes import pochta_mub
from app.users.utils.mub import MUBProtection

mub_router = APIRouterExt(prefix="/mub", dependencies=[MUBProtection])
mub_router.include_router(pochta_mub.router, prefix="/pochta-service")

api_router = APIRouterExt()
api_router.include_router(mub_router)


@asynccontextmanager
async def lifespan() -> AsyncIterator[None]:
    if PRODUCTION_MODE and not EMAIL_INITIALIZED:
        logging.warning("Configuration for email service is missing")
    yield