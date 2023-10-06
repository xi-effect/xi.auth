from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.common.config import DATABASE_RESET, PRODUCTION_MODE, Base, db_url, engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if not PRODUCTION_MODE:
        async with engine.begin() as conn:
            if db_url.endswith("app.db") or DATABASE_RESET:
                await conn.run_sync(Base.metadata.drop_all)
            if not db_url.startswith("postgresql") or DATABASE_RESET:
                await conn.run_sync(Base.metadata.create_all)

    yield


app = FastAPI(lifespan=lifespan)
