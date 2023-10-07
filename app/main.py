from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

from app.common.config import (
    DATABASE_RESET,
    PRODUCTION_MODE,
    Base,
    db_url,
    engine,
    sessionmaker,
)
from app.common.sqla import session_context
from app.routes import users_mub


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
app.include_router(users_mub.router, prefix="/mub/users")


@app.middleware("http")
async def database_session_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    async with sessionmaker.begin() as session:
        session_context.set(session)
        return await call_next(request)
