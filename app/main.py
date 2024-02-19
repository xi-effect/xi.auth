from asyncio import AbstractEventLoop, get_running_loop
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from aio_pika import connect_robust
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

from app.common.config import (
    DATABASE_MIGRATED,
    MQ_URL,
    PRODUCTION_MODE,
    Base,
    engine,
    pochta_producer,
    sessionmaker,
)
from app.common.sqla import session_context
from app.routes import (
    avatar_rst,
    current_user_rst,
    proxy_rst,
    reglog_rst,
    sessions_rst,
    users_mub,
)
from app.utils.cors import CorrectCORSMiddleware


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if not PRODUCTION_MODE and not DATABASE_MIGRATED:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    loop: AbstractEventLoop = get_running_loop()
    connection = await connect_robust(MQ_URL, loop=loop)
    await pochta_producer.connect(connection)

    yield
    await connection.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CorrectCORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API
app.include_router(reglog_rst.router, prefix="/api")
app.include_router(current_user_rst.router, prefix="/api/users/current")
app.include_router(sessions_rst.router, prefix="/api/sessions")
app.include_router(avatar_rst.router, prefix="/api/users/image")

# MUB
app.include_router(users_mub.router, prefix="/mub/users")

# Proxy
app.include_router(proxy_rst.router, prefix="/proxy/auth")


@app.middleware("http")
async def database_session_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    async with sessionmaker.begin() as session:
        session_context.set(session)
        return await call_next(request)
